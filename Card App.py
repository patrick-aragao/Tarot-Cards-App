import os
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from random import shuffle
import openai
from openai import OpenAI
import csv
import pandas as pd
from io import StringIO
from dotenv import load_dotenv


class TarotApp:
    def __init__(self, root, user_name, user_question):
        self.root = root
        self.root.title("Tarot Card App")
        self.deck = list(range(1, 45))  # 44 cards, so end at 45
        self.split_decks = []
        self.selected_cards = []
        self.user_name = user_name
        self.user_question = user_question

        self.card_data = {}
        self.card_buttons = []

        self.ai_dialog = None
        self.card_dialog = None

        self.gpt_interpretation = None
        self.card_interpretations = None

        # Introduce the can_select_cards variable
        self.can_select_cards = False

        # Initialize UI
        self.init_ui()
        shuffle(self.deck)
        
        # Read the CSV file and assign to self.card_data
        file_path = "cards_meaning.csv"  # Adjust path if necessary
        csv_data = pd.read_csv(file_path)
        self.card_data = csv_data.to_dict(orient="records")
        #print(csv_data.columns)
    
    # Load the .env file
    load_dotenv()
    
    client = OpenAI(
        api_key = os.getenv("open_ai_api_key")
    )
    
    def show_card_meaning(self):
        if self.card_interpretations is None:
            return

        if hasattr(self, 'card_dialog') and self.card_dialog and self.card_dialog.winfo_exists():
            self.card_dialog.focus_set()  # If the window is still open, bring it to focus
        else:
            self.card_dialog = self.show_dialog("info", "Card Interpretation", self.card_interpretations)  # Create a new window

        self.check_window_status()

    def show_ai_interpretation_window(self):
        if self.gpt_interpretation is None:
            return
        
        if hasattr(self, 'ai_dialog') and self.ai_dialog and self.ai_dialog.winfo_exists():
            self.ai_dialog.focus_set()  # If the window is still open, bring it to focus
        else:
            self.ai_dialog = self.show_ai_interpretation(self.gpt_interpretation)  # Create a new window

        self.check_window_status()
    
    def show_dialog(self, dialog_type, title, message, **kwargs):
        dialog = None
        if dialog_type == "info":
            dialog = tk.Toplevel(self.root)
            dialog.title(title)
            
            text_widget = tk.Text(dialog, wrap=tk.WORD, width=60, height=20)
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, message)
            text_widget.config(state=tk.DISABLED)  # Make it read-only
            
            scrollbar = tk.Scrollbar(dialog, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget.config(yscrollcommand=scrollbar.set)
            
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.bind("<Destroy>", self.on_window_close)

        elif dialog_type == "warning":
            messagebox.showwarning(title, message)
            self.root.focus_force()
        elif dialog_type == "error":
            messagebox.showerror(title, message)
            self.root.focus_force()
        return dialog

    def init_ui(self):
        
        # Create a main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        # Create a canvas
        self.canvas = tk.Canvas(self.main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Add a scrollbar to the canvas
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create a frame inside the canvas to hold other widgets
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.inner_frame, anchor="nw")

        # Adjust all your widgets to pack/grid inside the `self.inner_frame`
        welcome_label = tk.Label(self.root, text=f"Hello {self.user_name}! Let's see what the cards has to say in regards your question:\n{self.user_question}", wraplength=300)
        welcome_label.pack(in_=self.inner_frame, pady=(10, 10))  # Adjust 50 to your desired value

        self.shuffle_button = tk.Button(self.inner_frame, text="1 - Shuffle the Deck", command=self.shuffle_deck)
        self.shuffle_button.pack(pady=5)

        self.split_button = tk.Button(self.inner_frame, text="2 - Split the Deck in 3 Parts", command=self.split_deck)
        self.split_button.pack(pady=5)

        self.assemble_button = tk.Button(self.inner_frame, text="3 - Regroup the Deck", command=self.assemble_deck)
        self.assemble_button.pack(pady=5)

        # Adding card counter
        self.card_count = 0
        self.card_counter_label = tk.Label(self.inner_frame, text=f"Cards Selected: {self.card_count}/9")
        self.card_counter_label.pack(pady=5)

        self.cards_frame = tk.Frame(self.inner_frame)
        self.cards_frame.pack(pady=5)

        # Add a button to upload CSV and get card interpretation
        self.interpret_button = tk.Button(self.inner_frame, text="4 - Interpret Selected Cards", command=self.interpret_selected_cards)
        self.interpret_button.pack(pady=5)

        # 3x3 matrix for showing selected cards
        self.matrix_frame = tk.Frame(self.inner_frame)
        self.matrix_frame.pack(pady=5)
        self.matrix_buttons = []
        self.matrix_canvases = []

        for i in range(3):
            row_buttons = []
            row_canvases = []
            for j in range(3):
                canvas = tk.Canvas(self.matrix_frame, width=80, height=80)
                btn = tk.Button(canvas, text="?", width=4, height=2, state=tk.DISABLED, bg="black", fg="white")
                canvas.create_window(40, 40, window=btn)  # Adjusted the Y position here to center the button a bit more
                sequence_text = canvas.create_text(40, 10, text=str(i*3 + j + 1), font=("Arial", 14), fill="white")
                canvas.sequence_text = sequence_text  # Store the text ID for later use
                canvas.grid(row=i, column=j, padx=5, pady=5)
                row_buttons.append(btn)
                row_canvases.append(canvas)
            self.matrix_buttons.append(row_buttons)
            self.matrix_canvases.append(row_canvases)

        for i, card_num in enumerate(self.deck):
            btn = tk.Button(self.cards_frame, text=str(card_num), width=4, height=2, command=lambda i=i, card_num=card_num: self.select_card(i))
            btn.grid(row=i//7, column=i%7, padx=5, pady=5)
            self.card_buttons.append(btn)

        self.buttons_frame = tk.Frame(self.inner_frame)  # Create a new frame
        self.buttons_frame.pack(pady=5, expand=True, anchor=tk.CENTER)  # pack the frame with expand=True

        # Reopen Card and AI Interpretation
        self.btn_card_meaning = tk.Button(self.buttons_frame, text="Card Interpretation", command=self.show_card_meaning)
        self.btn_card_meaning.config(state=tk.DISABLED)
        self.btn_card_meaning.grid(row=0, column=0, padx=10)

        self.btn_ai_interpretation = tk.Button(self.buttons_frame, text="AI Interpretation", command=self.show_ai_interpretation_window)
        self.btn_ai_interpretation.config(state=tk.DISABLED)
        self.btn_ai_interpretation.grid(row=0, column=1, padx=10)
        
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def shuffle_deck(self):
        for btn in self.card_buttons:
            btn.config(text="?")

        if self.shuffle_button['state'] == tk.DISABLED:
            self.show_dialog("warning", "Warning", "You cannot perform this action 2 times.")
            return

        shuffle(self.deck)
        self.shuffle_button.config(state=tk.DISABLED)
        self.show_dialog("warning", "Warning", "Deck shuffled successfully!")

        self.check_actions_done()

    def split_deck(self):
        if self.split_button['state'] == tk.DISABLED:
            self.show_dialog("warning", "Warning", "You cannot perform this action 2 times.")
            return

        while True:
            percent1 = simpledialog.askfloat("Input", "Enter percentage for first split (e.g., 40 for 40%):", parent=self.root)
            if percent1 is not None and 0 <= percent1 <= 100:
                break
            self.show_dialog("warning", "Warning", "Please provide a valid percentage between 0 and 100.")

        while True:
            percent2 = simpledialog.askfloat("Input", "Enter percentage for second split (remaining percentage is for third split):", parent=self.root)
            if percent2 is not None and 0 <= percent2 <= 100 and (percent1 + percent2) <= 100:
                break
            self.show_dialog("warning", "Warning", "Please provide a valid percentage between 0 and 100 that, when added to the first percentage, doesn't exceed 100.")

        count1 = int(len(self.deck) * percent1 / 100)
        count2 = int(len(self.deck) * percent2 / 100)
        count3 = len(self.deck) - count1 - count2

        self.split_decks = [self.deck[:count1], self.deck[count1:count1+count2], self.deck[count1+count2:]]

        self.split_button.config(state=tk.DISABLED)
        self.show_dialog("warning", "Warning", f"Decks split into {count1}, {count2}, {count3} cards.")

        self.check_actions_done()

    def assemble_deck(self):
        if self.assemble_button['state'] == tk.DISABLED:
            self.show_dialog("warning", "Warning", "You cannot perform this action 2 times.")
            return

        # Add a loop to repeatedly prompt the user until a valid response is provided.
        while True:
            order = simpledialog.askstring("Input", "Enter order to assemble the deck (e.g.: 123, 213, 312 etc.)", parent=self.root)
            
            if order is None:  # If the user closes the dialog or clicks "Cancel"
                self.show_dialog("warning", "Warning", "Please provide a valid order (e.g.: 123, 213, 312).")
                continue

            if len(order) == 3 and set(order) == {"1", "2", "3"}:
                break  # If the order is valid, break out of the loop
            else:
                self.show_dialog("error", "Error", "Invalid order. Please enter a permutation of '123'")

        self.deck = []
        for ch in order:
            self.deck.extend(self.split_decks[int(ch) - 1])

        self.assemble_button.config(state=tk.DISABLED)
        self.show_dialog("warning", "Warning", "Deck assembled successfully!")

        self.check_actions_done()

    def select_card(self, idx):
        # Check if cards can be selected based on actions
        if not self.can_select_cards:
            self.root.after(1, lambda: messagebox.showwarning("Warning", "Please shuffle, split, and assemble the deck before selecting cards."))
            return
            
        # Prevent selecting more than 9 cards
        if self.card_count >= 9:
            self.root.after(1, lambda: messagebox.showwarning("Warning", "You have already selected 9 cards."))
            return

        # Check if the card is already selected
        card = self.deck[idx]
        if card in self.selected_cards:
            return
            
        self.selected_cards.append(card)
        self.card_buttons[idx].config(text=str(card), state=tk.DISABLED)

        # Increase card count and update the label
        self.card_count += 1
        self.card_counter_label.config(text=f"Cards Selected: {self.card_count}/9")

        # Logic to change appearance after 9 cards are selected
        if len(self.selected_cards) == 9:
            for btn in self.card_buttons:
                if btn['state'] == tk.DISABLED:  # This is a selected card
                    btn.config(fg='black', bg='white', state=tk.NORMAL)
                else:  # This is a non-selected card
                    btn.config(fg='white', bg='gray', state=tk.DISABLED)

            # Populate the 3x3 matrix with the selected cards
            for i in range(3):
                for j in range(3):
                    card_num = i * 3 + j
                    self.matrix_buttons[i][j].config(text=str(self.selected_cards[card_num]), bg="white", fg="black", state=tk.NORMAL)

    def check_actions_done(self):
        """Check if all actions (shuffle, split, assemble) are done."""
        if self.shuffle_button['state'] == tk.DISABLED and \
           self.split_button['state'] == tk.DISABLED and \
           self.assemble_button['state'] == tk.DISABLED:
           self.can_select_cards = True
    
    def make_text_context_menu(self, text_widget):
        context_menu = tk.Menu(text_widget, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: text_widget.event_generate("<<Copy>>"))
        
        def on_context_menu(event):
            text_widget.config(state=tk.NORMAL)
            # Force focus to the parent of the text widget (the AI Interpretation window)
            text_widget.master.focus_set()
            context_menu.post(event.x_root, event.y_root)
            text_widget.config(state=tk.DISABLED)  # Set it back to DISABLED after showing the menu
            
        text_widget.bind("<Button-3>", on_context_menu)
        text_widget.bind("<Control-Button-1>", on_context_menu)  # For macOS
         
    def get_tarot_interpretation(self, user_name, question, cards, card_data):
        card_names = [self.get_card_details_by_number(str(card_number), card_data)['card_name'] for card_number in cards]
        spread = ', '.join(card_names)  # Use card names instead of numbers
        messages = [
        {"role": "system", "content": "You are a helpful and very wise assistant that interprets tarot card spreads from the Gilded Reverie Lenormand Expanded Edition using the simple nine card spread."},
        {"role": "user", "content": f"My name is {user_name} and I've drawn a 3x3 tarot spread: {spread}. I want to know: {question}."},
        ]
        print(card_names)
        print(spread)
        print(messages)
        # Print the messages to the console

        response = self.client.chat.completions.create(model="gpt-4", messages=messages)
        
        interpretation = interpretation = response.choices[0].message.content.strip()

        # Ensuring a polite and nice tone
        final_response = f"{interpretation} . I hope this interpretation provides to you some clarity. Thanks for using our App and have a nice day!"

        return final_response
    
    def show_ai_interpretation(self, message):
        dialog = tk.Toplevel(self.root)
        dialog.title("AI Interpretation")

        text_widget = tk.Text(dialog, wrap=tk.WORD, width=60, height=20)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, message)
        text_widget.config(state=tk.NORMAL)  # Make it read-only
        
        self.make_text_context_menu(text_widget)

        scrollbar = tk.Scrollbar(dialog, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.config(yscrollcommand=scrollbar.set)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        dialog.bind("<Destroy>", self.on_window_close)
        return dialog
    
    @staticmethod
    def get_card_details_by_number(card_number, data):
        for row in data:
            if int(row['card_number']) == int(card_number):
                return row
        return None
    
    def interpret_selected_cards(self):
        # Check if cards have been selected
        if len(self.selected_cards) != 9:
            self.show_dialog("warning", "Warning", "Please select 9 cards before interpreting.")
            return

        #self.card_data = self.load_embedded_csv_data(csv_data_string)
        interpretations = []

        for card_number in self.selected_cards:
            card_details = self.get_card_details_by_number(str(card_number), self.card_data)
            if card_details:
                interpretations.append(f"Card {card_number}: {card_details['card_name']}\nMeaning: {card_details['card_meaning']}\n\nDetails: {card_details['card_detail']}\n\n")
            else:
                interpretations.append(f"Card: {card_number}\nNo details found in the provided CSV.\n\n")

        interpretation_text = "".join(interpretations)
        self.card_interpretations = interpretation_text

        # Disable the card meaning button before showing the pop-up
        self.interpret_button.config(state=tk.DISABLED)

        try:
            # Get GPT-based interpretation
            gpt_interpretation = self.get_tarot_interpretation(self.user_name, self.user_question, self.selected_cards, self.card_data)
            self.gpt_interpretation = gpt_interpretation
            self.show_dialog("info", "AI Interpretation", gpt_interpretation)
        except openai.RateLimitError:
            self.show_dialog("error", "Error", "Could not get an AI interpretation due to an internal error. Please try again later.")
            
        # Show the pop-up with card meanings
        self.show_dialog("info", "Card Interpretation", interpretation_text)

        self.btn_card_meaning.config(state=tk.NORMAL)
        self.btn_ai_interpretation.config(state=tk.NORMAL)

    def on_window_close(self, event):
        # Activate the reopen button when any window is closed
        self.check_window_status()

    def check_window_status(self):
        if hasattr(self, 'card_dialog') and self.card_dialog and self.card_dialog.winfo_exists():
            self.btn_card_meaning.config(state=tk.DISABLED)
        else:
            self.btn_card_meaning.config(state=tk.NORMAL)

        if hasattr(self, 'ai_dialog') and self.ai_dialog and self.ai_dialog.winfo_exists():
            self.btn_ai_interpretation.config(state=tk.DISABLED)
        else:
            self.btn_ai_interpretation.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x1000")  # Set default window size LxH
    root.withdraw()  # Temporarily hide the main window
    
    while True:
        user_name = simpledialog.askstring("Input", "What is Your Name?", parent=root)
        if user_name and user_name.strip():
            break
        elif user_name is None:
            root.destroy()
            exit()
        else:
            messagebox.showwarning("Warning", "Please provide a valid name.")

    while True:
        user_question = simpledialog.askstring("Input", "What is your question?", parent=root)
        if user_question and user_question.strip():
            break
        elif user_question is None:
            root.destroy()
            exit()
        else:
            messagebox.showwarning("Warning", "Please provide a valid question.")

    root.deiconify()  # Show the main window again
    app = TarotApp(root, user_name, user_question)
    root.mainloop()

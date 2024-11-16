# ------------------------------------------   ------------------- #
#    ___      _ _           _   _  __         |                    #
#   / __\___ | | | ___  ___| |_(_)/ _|_   _   | Powered by: fghio  #
#  / /  / _ \| | |/ _ \/ __| __| | |_| | | |  | Version   : 1.0    #
# / /__| (_) | | |  __/ (__| |_| |  _| |_| |  |                    #
# \____/\___/|_|_|\___|\___|\__|_|_|  \__, |  | MM/YY     : 11/24  #
#                                     |___/   |                    #
#--------------------------------------------   ------------------ #

import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import threading

class ItemTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Item Tracker")
        self.root.geometry("800x600")

        # Folder to store JSON files and images
        self.lists_folder = 'lists'
        self.images_folder = 'images'
        if not os.path.exists(self.lists_folder):
            os.makedirs(self.lists_folder)
        if not os.path.exists(self.images_folder):
            os.makedirs(self.images_folder)

        # Scrollable frame for list cards
        self.canvas = tk.Canvas(root)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        # Scrollbar
        scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Display available lists
        self.display_lists()

        # <Floating> "+" button in the bottom-right corner
        plus_button = tk.Button(root, text="+", font=("Arial", 20), command=self.create_list)
        plus_button.place(relx=0.95, rely=0.95, anchor="se")

    def display_lists(self):
        """Displays available lists in a grid format with images 
        in a scrollable environment."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Read available lists in list folder
        available_lists = [f for f in os.listdir(self.lists_folder) if f.endswith('.json')]

        # If no list available
        if not available_lists:
            no_list_label = tk.Label(self.scrollable_frame, text="No lists available.")
            no_list_label.pack()
            return

        # otherwise
        for idx, filename in enumerate(available_lists):
            list_name = filename.replace(".json", "").replace("_", " ").title()

            # we need name and image (default if not connected image)
            with open(os.path.join(self.lists_folder, filename), 'r') as file:
                data = json.load(file)
                image_filename = data.get('image', 'default.png')

            image_path = os.path.join(self.images_folder, image_filename)
            try:
                img = Image.open(image_path)
            except FileNotFoundError:
                img = Image.open("default.png")
            img = img.resize((90, 120), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # clickable list box
            list_button = tk.Button(
                self.scrollable_frame,
                text=list_name,
                image=photo,
                compound="top",
                command=lambda filename=filename: self.open_list(filename)
            )
            list_button.image = photo
            list_button.grid(row=idx // 5, column=idx % 5, padx=10, pady=10, sticky="nsew")

    def create_list(self):
        """Opens a form to create a new list with name, item count, and optional picture."""
        form_window = tk.Toplevel(self.root)
        form_window.title("Create New List")
        form_window.geometry("400x300")

        tk.Label(form_window, text="List Name:").pack(pady=5)
        list_name_entry = tk.Entry(form_window, width=30)
        list_name_entry.pack()

        tk.Label(form_window, text="Number of Items:").pack(pady=5)
        item_count_entry = tk.Entry(form_window, width=30)
        item_count_entry.pack()

        # Image is either default, or provided by user.
        image_path = None
        def select_image():
            nonlocal image_path
            image_path = filedialog.askopenfilename(
                title="Select a picture",
                filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
            )
            if image_path:
                img = Image.open(image_path)
                photo = ImageTk.PhotoImage(img)
                image_label.config(image=photo)
                image_label.image = photo
                # if provided image, window is resized
                form_window.geometry("400x680")


        tk.Button(form_window, text="Select Image", command=select_image).pack(pady=5)
        image_label = tk.Label(form_window)
        image_label.pack()

        def save_list():
            '''Save the list, with several checks'''
            list_name = list_name_entry.get()
            try:
                end_value = int(item_count_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Number of items must be an integer.")
                return

            if not list_name or not end_value:
                messagebox.showerror("Error", "List name and number of items are required.")
                return

            if not image_path:
                image_filename = "default.png"
            else:
                image = Image.open(image_path)
                image_filename = f"{list_name.lower().replace(' ', '_')}.png"
                image.save(os.path.join(self.images_folder, image_filename))

            # Create the json file
            list_filename = list_name.lower().replace(" ", "_") + ".json"
            list_path = os.path.join(self.lists_folder, list_filename)
            data = {
                'list_name': list_name,
                'total': list(range(1, end_value + 1)),
                'possessed': [],
                'missing': list(range(1, end_value + 1)),
                'image': image_filename
            }
            with open(list_path, 'w') as file:
                json.dump(data, file, indent=4)

            # In case of success
            messagebox.showinfo("Success", f"List '{list_name}' created!")
            form_window.destroy()
            self.display_lists()

        tk.Button(form_window, text="Create List", command=save_list).pack(pady=20)

    def open_list(self, filename):
        """Open and display the list items in a new window with buttons to modify the list."""
        list_window = tk.Toplevel(self.root)
        list_window.title("Loading...")
        loading_label = tk.Label(list_window, text="Loading, please wait...")
        loading_label.pack(pady=10)

        def load_data():
            list_path = os.path.join(self.lists_folder, filename)
            with open(list_path, 'r') as file:
                data = json.load(file)
            self.root.after(0, lambda: self.display_list_window(data, list_window))

        threading.Thread(target=load_data).start()

    def display_list_window(self, data, list_window):
        '''Actual display window - level 2 of the app'''
        list_window.title(data['list_name'])
        for widget in list_window.winfo_children():
            widget.destroy()

        # Setting the desired size for the image and loading it
        desired_size = (270, 340)
        image_path = os.path.join(self.images_folder, data['image'])
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            image = Image.open("default.png")

        image = image.resize(desired_size, Image.Resampling.LANCZOS)

        # Fill the window: picture
        photo = ImageTk.PhotoImage(image)
        image_label = tk.Label(list_window, image=photo)
        image_label.image = photo
        image_label.grid(row=0, column=0, padx=(20,10), pady=(20,10))

        # Fill the window: list of buttons
        button_panel = tk.Frame(list_window)
        button_panel.grid(row=0, column=1, padx=10, sticky="nw")

        def rename_list():
            new_name = simpledialog.askstring("Rename", "Enter new list name:")
            if new_name:
                new_filename = new_name.lower().replace(" ", "_") + ".json"
                os.rename(os.path.join(self.lists_folder, data['list_name'].lower().replace(" ", "_") + ".json"), 
                          os.path.join(self.lists_folder, new_filename))
                data['list_name'] = new_name
                with open(os.path.join(self.lists_folder, new_filename), 'w') as file:
                    json.dump(data, file, indent=4)
                self.display_lists()

        def delete_list():
            #TODO: request "Are you sure?"
            os.remove(os.path.join(self.lists_folder, data['list_name'].lower().replace(" ", "_") + ".json"))
            list_window.destroy()
            self.display_lists()

        def reset_list():
            #TODO: request "Are you sure?"
            data['possessed'] = []
            data['missing'] = data['total']
            with open(os.path.join(self.lists_folder, data['list_name'].lower().replace(" ", "_") + ".json"), 'w') as file:
                json.dump(data, file, indent=4)
            self.display_list_window(data, list_window)

        def add_owned():
            """Open a new window to allow the user to add items they now own."""
            input_window = tk.Toplevel(self.root)
            input_window.title("Add Owned Items")
            input_window.geometry("350x200")

            tk.Label(input_window, text="Items now owned (comma-separated or range):").pack(pady=10)
            input_entry = tk.Entry(input_window, width=30)
            input_entry.pack(pady=10)

            def parse_input(input_text):
                """Parse user input to handle both comma-separated values and ranges."""
                items = set()  # Use a set to avoid duplicates!
                for part in input_text.split(','):
                    part = part.strip()
                    if '-' in part:  # Check if the input has a range!
                        try:
                            start, end = map(int, part.split('-'))
                            if start > end:
                                raise ValueError(f"Invalid range: {part}")
                            items.update(range(start, end + 1))  # Add the full range to the set!
                        except ValueError:
                            raise ValueError(f"Invalid range format: {part}")
                    else:
                        try:
                            items.add(int(part))  # Add single numbers to the set!
                        except ValueError:
                            raise ValueError(f"Invalid number: {part}")
                return sorted(items)  # Return a sorted list!

            def submit_items():
                user_input = input_entry.get().strip()
                if not user_input:
                    messagebox.showerror("Error", "No items entered.")
                    return

                try:
                    # Parse the input
                    item_numbers = parse_input(user_input)
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return

                # Validate input
                invalid_items = [item for item in item_numbers if item not in data['total'] or item in data['possessed']]
                if invalid_items:
                    messagebox.showerror(
                        "Error",
                        f"The following items are invalid or already owned: {', '.join(map(str, invalid_items))}"
                    )
                    return

                # Update possession data
                data['possessed'].extend(item_numbers)
                data['missing'] = [item for item in data['total'] if item not in data['possessed']]

                # Save changes to JSON file
                list_path = os.path.join(self.lists_folder, data['list_name'].lower().replace(" ", "_") + ".json")
                with open(list_path, 'w') as file:
                    json.dump(data, file, indent=4)

                messagebox.showinfo("Success", "Items added to your possession!")
                input_window.destroy()
                self.display_list_window(data, list_window)

            tk.Button(input_window, text="Submit", command=submit_items).pack(pady=20)

        def remove_owned():
            """Removes items from the 'possessed' list and updates the view.
            Currently: only comma separated elements (for safety reasons)"""
            remove_window = tk.Toplevel(list_window)
            remove_window.title("Remove Owned Items")
            remove_window.geometry("350x150")

            tk.Label(remove_window, text="Items not owned anymore (comma-separated):").pack(pady=10)
            item_entry = tk.Entry(remove_window, width=30)
            item_entry.pack(pady=5)

            def process_removal():
                items_to_remove = item_entry.get()
                try:
                    items_to_remove = list(map(int, items_to_remove.split(',')))
                except ValueError:
                    messagebox.showerror("Error", "Please enter valid numbers separated by commas.")
                    return

                invalid_items = [item for item in items_to_remove if item not in data['possessed']]
                if invalid_items:
                    messagebox.showerror("Error", f"The following items are not in the owned list: {invalid_items}")
                    return

                # Remove items from possessed and add back to missing
                for item in items_to_remove:
                    data['possessed'].remove(item)
                    data['missing'].append(item)

                # Sort missing list for consistency
                data['missing'].sort()

                # Save changes
                with open(os.path.join(self.lists_folder, data['list_name'].lower().replace(" ", "_") + ".json"), 'w') as file:
                    json.dump(data, file, indent=4)

                messagebox.showinfo("Success", "Selected items removed from owned list.")
                remove_window.destroy()
                self.display_list_window(data, list_window)  # Refresh the list window

            tk.Button(remove_window, text="Remove", command=process_removal).pack(pady=10)

        tk.Button(button_panel, text="Rename", command=rename_list).pack(fill="x", pady=(20,5))
        tk.Button(button_panel, text="Delete", command=delete_list).pack(fill="x", pady=5)
        tk.Button(button_panel, text="Reset", command=reset_list).pack(fill="x", pady=5)

        tk.Button(button_panel, text="Own +", command=add_owned).pack(fill="x", pady=5)
        tk.Button(button_panel, text="Own -", command=remove_owned).pack(fill="x", pady=5)

        # Completion Bar
        def update_completion_bar():
            total_items = len(data['total'])
            owned_items = len(data['possessed'])
            completion_percentage = int((owned_items / total_items) * 100)
            progress_bar['value'] = completion_percentage
            completion_label.config(text=f"{completion_percentage}% completed")

        progress_bar = ttk.Progressbar(button_panel, orient="horizontal", length=70, mode="determinate")
        progress_bar.pack(padx=5, pady=(10,5), fill="x", expand=True)
        completion_label = tk.Label(button_panel, text="0% completed")
        completion_label.pack(fill="x", pady=(0,5))

        # Initial update of completion bar
        update_completion_bar()

        # Dropdown Menu for Filtering
        filter_options = ["All", "I own", "I miss"]
        filter_var = tk.StringVar(value=filter_options[0])  # Default: All items

        # Scrollable area for list items with 4 items per row, color-coded for possession status
        items_canvas = tk.Canvas(list_window, width=400, height=200)
        items_frame = tk.Frame(items_canvas)
        scrollbar = tk.Scrollbar(list_window, orient="vertical", command=items_canvas.yview)
        items_canvas.configure(yscrollcommand=scrollbar.set)

        items_canvas.grid(row=1, column=0, columnspan=2)
        scrollbar.grid(row=1, column=2, sticky="nese")
        items_canvas.create_window((0, 0), window=items_frame, anchor="nw")

        # Function to enable scrolling using the trackpad (mouse wheel)
        def on_canvas_scroll(event):
            """Scroll the canvas with the trackpad or mouse wheel. 
            TODO: improve"""
            items_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind the scroll event to the canvas
        items_canvas.bind_all("<Button-4>", on_canvas_scroll)  # Scroll up
        items_canvas.bind_all("<Button-5>", on_canvas_scroll)  # Scroll down

        def update_items_display():
            """Update the items displayed based on the selected filter."""
            for widget in items_frame.winfo_children():
                widget.destroy()

            selected_filter = filter_var.get()

            # Determine which list of items to display based on the filter
            if selected_filter == "All":
                items_to_display = data['total']
            elif selected_filter == "I own":
                items_to_display = data['possessed']
            elif selected_filter == "I miss":
                items_to_display = data['missing']
            else:
                items_to_display = []

            # Add each item to the grid, with appropriate color
            for idx, item in enumerate(items_to_display):
                color = "green" if item in data['possessed'] else "gray"
                item_label = tk.Label(items_frame, text=str(item), width=5, bg=color, fg="white")
                item_label.grid(row=idx // 7, column=idx % 7, padx=5, pady=5)

            # Update the canvas scroll region to include all items
            items_frame.update_idletasks()
            items_canvas.configure(scrollregion=items_canvas.bbox("all"))

        # Create filter dropdown menu
        filter_menu = tk.OptionMenu(button_panel, filter_var, *filter_options, command=lambda _: update_items_display())
        filter_menu.pack(fill="x", pady=5)

        # Initial Display of All Items
        update_items_display()

        
        
app = ItemTrackerApp(tk.Tk())
app.root.mainloop()

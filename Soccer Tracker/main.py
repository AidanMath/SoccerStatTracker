import os
import requests
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Label, Frame, Canvas, Text
from PIL import Image, ImageTk, ImageEnhance
import http.client
import json

leagues_info = {
    "Premier League": {"id": "39", "logo": "PremierLeague.png"},
    "La Liga": {"id": "140", "logo": "LaLiga.png"},
    "Ligue 1": {"id": "61", "logo": "Ligue1.png"},
    "Serie A": {"id": "135", "logo": "SeriaA.png"},
    "Bundesliga": {"id": "78", "logo": "Bundesliga.png"}
}

API_KEY = os.environ.get('FOOTBALL_API_KEY')
if not API_KEY:
    raise ValueError("API Key not found in environment variables")

headers = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

class LeagueGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Top 5 Leagues Stats")
        self.master.geometry("600x770")

        self.tree_frame = tk.Frame(master)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        self.tree = ttk.Treeview(self.tree_frame, columns=("League",), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        self.image_refs = {}  
        self.load_leagues()

        self.selection_frame = tk.Frame(master)
        self.selection_frame.pack(pady=20)

        self.selected_label = tk.Label(self.selection_frame, text="")
        self.selected_label.pack()

        self.year_label = tk.Label(self.selection_frame, text="Enter Season:")
        self.year_label.pack()

        self.year_entry = tk.Entry(self.selection_frame)
        self.year_entry.pack()

        self.submit_button = tk.Button(self.selection_frame, text="Finalize", command=self.Load_league_season)
        self.submit_button.pack()

        self.selected_league = None

    def load_leagues(self):
        style = ttk.Style()
        style.configure("Treeview", rowheight=60, font=('Arial', 10, 'bold'))
        
        dark_green = '#1B8A4A' 
        light_green = '#2ECC71'  
        
        for i, (league_name, info) in enumerate(leagues_info.items()):
            img = Image.open(info["logo"])
            img = img.resize((50, 50), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            tag = f"row{i % 2}"
            item = self.tree.insert("", tk.END, values=(league_name,), image=photo, tags=(tag, "selectable"))
           
            self.image_refs[league_name] = photo

            self.tree.insert("", tk.END, text="", values=(" ",), tags=(f"spacer{i % 2}",))

        self.tree.tag_configure("row0", background=dark_green, foreground="white")
        self.tree.tag_configure("row1", background=dark_green, foreground="white")
        self.tree.tag_configure("spacer0", background=light_green)
        self.tree.tag_configure("spacer1", background=light_green)
        
        self.tree.tag_bind("spacer0", "<<TreeviewSelect>>", self.prevent_spacer_selection)
        self.tree.tag_bind("spacer1", "<<TreeviewSelect>>", self.prevent_spacer_selection)

    def prevent_spacer_selection(self, event):
        self.tree.selection_remove(self.tree.selection())

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            league_name = self.tree.item(selected_item)["values"][0]
            if league_name and league_name.strip() != "":
                self.selected_label.config(text=f"Selected League: {league_name}")
                self.selected_league = leagues_info[league_name]["id"]
                self.year_label.config(text="Enter Season Year:")
            else:
                self.tree.selection_remove(selected_item)

    def Load_league_season(self):
        if not self.selected_league:
            messagebox.showerror("Error", "Please select a league first")
            return

        year = self.year_entry.get()
        if not year.isdigit():
            messagebox.showerror("Invalid input", "Please enter a valid year")
            return

        conn = http.client.HTTPSConnection("v3.football.api-sports.io")

        endpoint = f"/standings?league={self.selected_league}&season={year}"
        
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read().decode("utf-8")

        if res.status == 200:
            json_data = json.loads(data)
            self.display_standings(json_data, year)
        else:
            messagebox.showerror("Error", f"Failed to fetch data: {res.status} {res.reason}")

        conn.close()

    def create_gradient(self, canvas, color1, color2, width, height):
        r1, g1, b1 = self.master.winfo_rgb(color1)
        r2, g2, b2 = self.master.winfo_rgb(color2)
        r_ratio = (r2 - r1) / height
        g_ratio = (g2 - g1) / height
        b_ratio = (b2 - b1) / height
        for i in range(height):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f'#{nr:04x}{ng:04x}{nb:04x}'
            canvas.create_line(0, i, width, i, fill=color)


    def display_standings(self, data, year):
        standings_window = Toplevel(self.master)
        standings_window.title(f"{self.get_league_name()} Standings {year}")
        standings_window.geometry("750x1100")
        standings_window.attributes('-alpha', 0.9)

        standings = data['response'][0]['league']['standings']
        if isinstance(standings, list) and len(standings) > 0:
            standings = standings[0]

        sorted_standings = sorted(standings, key=lambda x: int(x.get('points', '0')), reverse=True)

        colors = self.get_league_colors()

        canvas = Canvas(standings_window, width=750, height=1100, bg=colors['bg'])  # Set bg color here
        canvas.pack(fill="both", expand=True)

        self.create_gradient(canvas, colors['bg'], colors['gradient_end'], 750, 1100)

        # Create a main frame to hold both headers and table
        main_frame = Frame(canvas, bg='white')
        main_frame.place(relx=0.5, rely=0.4, anchor="center")

        headers = ['Pos', 'Team', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
        for col, header in enumerate(headers):
            Label(main_frame, text=header, font=('Arial', 10, 'bold'), 
                    bg='white', fg='black').grid(row=0, column=col, padx=5, pady=5, sticky='w')

        for row, team in enumerate(sorted_standings, start=1):
            bg_color = 'white' if row % 2 == 0 else '#f0f0f0'
            Label(main_frame, text=str(row), bg=bg_color, fg=colors['text']).grid(row=row, column=0, padx=5, pady=2, sticky='w')
            Label(main_frame, text=team.get('team', {}).get('name', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=1, padx=5, pady=2, sticky='w')
            
            all_stats = team.get('all', {})
            Label(main_frame, text=all_stats.get('played', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=2, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('win', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=3, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('draw', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=4, padx=5, pady=2)
            Label(main_frame, text=all_stats.get('lose', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=5, padx=5, pady=2)
            
            goals = all_stats.get('goals', {})
            Label(main_frame, text=goals.get('for', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=6, padx=5, pady=2)
            Label(main_frame, text=goals.get('against', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=7, padx=5, pady=2)
            
            Label(main_frame, text=team.get('goalsDiff', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=8, padx=5, pady=2)
            Label(main_frame, text=team.get('points', ''), bg=bg_color, fg=colors['text']).grid(row=row, column=9, padx=5, pady=2)

        analysis_frame = Frame(canvas, bg='white')
        analysis_frame.place(relx=0.5, rely=0.85, anchor="center", width=700)

        analysis_label = Label(analysis_frame, text="Type Team Name for Further Stats", bg='white', font=('Arial', 10, 'bold'))
        analysis_label.pack(pady=(10, 5))

        self.analysis_text = Text(analysis_frame, height=1, width=15)
        self.analysis_text.pack(pady=5)

        analysis_button = tk.Button(analysis_frame, text="More Info", command=self.get_analysis)
        analysis_button.pack(pady=5)

        button_frame = Frame(canvas, bg=colors['bg'])
        button_frame.place(relx=0.5, rely=0.95, anchor="center")

        for widget in main_frame.winfo_children():
            if isinstance(widget, Label) and widget.cget("text") not in headers:
                widget.bind("<Button-1>", lambda e, w=widget: self.on_team_select(w))

    def get_analysis(self):
        analysis_request = self.analysis_text.get("1.0", tk.END).strip()
        if analysis_request:
            # Here you would typically send this request to an API or process it
            # For now, we'll just show a message box with the request
            messagebox.showinfo("Analysis Request", f"Your request: {analysis_request}\n\nAnalysis processing is not implemented yet.")
        else:
            messagebox.showwarning("Empty Request", "Please enter an analysis request.")

    def get_league_name(self):
        for name, info in leagues_info.items():
            if info['id'] == self.selected_league:
                return name
        return "Unknown League"
        
    def get_league_colors(self):
        league_colors = {
            "39": {  # Premier League
                "bg": "#3D195B", "gradient_end": "#7F54B3", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "140": {  # La Liga
                "bg": "#EE8707", "gradient_end": "#FFC300", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "61": {  # Ligue 1
                "bg": "#091C3E", "gradient_end": "#1C4F9C", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "135": {  # Serie A
                "bg": "#008FD7", "gradient_end": "#60C8FF", "header_fg": "#FFFFFF", "text": "#000000"
            },
            "78": {  # Bundesliga
                "bg": "#D20515", "gradient_end": "#FF4D4D", "header_fg": "#FFFFFF", "text": "#000000"
            }
        }
        return league_colors.get(self.selected_league, league_colors["39"])  # Default to Premier League colors

    def on_team_select(self, widget):
        # Implementation needed
        pass

    
if __name__ == "__main__":
    root = tk.Tk()
    app = LeagueGUI(root)
    root.mainloop()
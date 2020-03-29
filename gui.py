import tkinter as tk

class RockEmSockEm(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, width=400,  height=400)

        self.label = tk.Label(self, text="Action: ", width=20)
        self.label.pack(fill="both", padx=100, pady=100)

        self.label.bind("<q>", self.on_wasd)
        self.label.bind("<w>", self.on_wasd)
        self.label.bind("<a>", self.on_wasd)
        self.label.bind("<s>", self.on_wasd)

        # give keyboard focus to the label by default, and whenever
        # the user clicks on it
        self.label.focus_set()
        self.label.bind("<1>", lambda event: self.label.focus_set())

        self.action_dict = {
            "q": "Block with left!",
            "w": "Block with right!",
            "a": "Punch with left!",
            "s": "Punch with right!"
        }

        # Initialize game
        # game = 

    def on_wasd(self, event):
        
        self.label.configure(text="Action: " + self.action_dict[event.keysym])

if __name__ == "__main__":
    root = tk.Tk()
    RockEmSockEm(root).pack(fill="both", expand=True)
    root.mainloop()
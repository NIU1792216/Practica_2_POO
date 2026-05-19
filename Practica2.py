# Practica 2
import os
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import pygame
from abc import ABC, abstractmethod

MUSIC_DIR = "MusicDir"
STATE_FILE = "state.json"

if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

pygame.mixer.init()

class MusicComponent(ABC):
    def __init__(self, name):
        self._name = name

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_length(self):
        pass

    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def get_elements(self):
        pass

class Song(MusicComponent):
    def __init__(self, name):
        super().__init__(name)

    def play(self):
        path = os.path.join(MUSIC_DIR, self._name)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        else:
            print(f"Error: No s'ha trobat el fitxer {self._name}")

    def stop(self):
        pygame.mixer.music.stop()

    def show(self):
        print(f"Cançó: {self._name}")

    def get_elements(self):
        return [self._name]

class PlayList(MusicComponent):
    def __init__(self, name):
        super().__init__(name)
        self._components = []

    def Add(self, element: MusicComponent):
        self._components.append(element)

    def remove_element(self, element: MusicComponent):
        if element in self._components:
            self._components.remove(element)

    def show(self):
        print(f"{self._name}")
        for comp in self._components:
            print("\t", end=" ")
            comp.show()

    def save_to_file(self):
        path = os.path.join(MUSIC_DIR, self._name)
        with open(path, 'w') as f:
            for comp in self._components:
                f.write(comp.name + '\n')

    def get_elements(self):
        elements = []
        for comp in self._components:
            elements.extend(comp.get_elements())
        return elements

    @property
    def components(self):
        return self._components

class Reproductor:
    def __init__(self):
        self._main_list = PlayList("MainList")
        self.update_state()

    def add(self, element: MusicComponent):
        self._main_list.Add(element)

    def remove(self, element: MusicComponent):
        self._main_list.remove_element(element)

    def get_all_songs_to_play(self):
        return self._main_list.get_elements()

    def stop(self):
        pygame.mixer.music.stop()

    def save_state(self):
        elements_names = [comp.name for comp in self._main_list.components]
        with open(STATE_FILE, 'w') as f:
            json.dump(elements_names, f)

    def update_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                try:
                    elements_names = json.load(f)
                    for name in elements_names:
                        if name.endswith('.mp3'):
                            self.add(Song(name))
                        elif name.endswith('.m3u'):
                            self.add(self._load_playlist_from_file(name))
                except json.JSONDecodeError:
                    pass

    def _load_playlist_from_file(self, filename):
        pl = PlayList(filename)
        path = os.path.join(MUSIC_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    if line.endswith('.mp3'):
                        pl.Add(Song(line))
                    elif line.endswith('.m3u'):
                        pl.Add(self._load_playlist_from_file(line))
        return pl


class Controller:
    def __init__(self, reproductor, view):
        self.reproductor = reproductor
        self.view = view
        
        self.playlist_queue = []
        self.is_playing = False

    def add_song(self, song_name):
        song = Song(song_name)
        self.reproductor.add(song)
        self.view.show_reproductor()

    def add_playlist(self, playlist_name):
        pl = self.reproductor._load_playlist_from_file(playlist_name)
        self.reproductor.add(pl)
        self.view.show_reproductor()

    def remove_element(self, index):
        if 0 <= index < len(self.reproductor.main_list.components):
            element = self.reproductor.main_list.components[index]
            self.reproductor.remove(element)
            self.view.show_reproductor()

    def create_playlist(self, name, selected_files):
        if not name.endswith('.m3u'):
            name += '.m3u'
        new_pl = PlayList(name)
        for file in selected_files:
            if file.endswith('.mp3'):
                new_pl.Add(Song(file))
            elif file.endswith('.m3u'):
                new_pl.Add(self.reproductor._load_playlist_from_file(file))
        new_pl.save_to_file()
        self.view.show_dir()

    def play(self):
        self.playlist_queue = self.reproductor.get_all_songs_to_play()
        if not self.playlist_queue:
            messagebox.showinfo("Avís", "No hi ha cançons per reproduir.")
            return
        
        self.is_playing = True
        self._play_next()

    def _play_next(self):
        if self.playlist_queue and self.is_playing:
            next_song = self.playlist_queue.pop(0)
            path = os.path.join(MUSIC_DIR, next_song)
            if os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self._check_music_end()
            else:
                self._play_next() 
        else:
            self.is_playing = False

    def _check_music_end(self):
        if self.is_playing:
            if not pygame.mixer.music.get_busy():
                self._play_next()
            else:
                self.view.root.after(1000, self._check_music_end)

    def stop(self):
        self.is_playing = False
        self.playlist_queue = []
        self.reproductor.stop()

    def exit(self):
        self.stop()
        self.reproductor.save_state()
        self.view.root.destroy()


class View:
    def __init__(self, root):
        self.root = root
        self.root.title("Reproductor de Música - MATCAD")
        self.root.geometry("500x500")
        self.controller = None

        frame_lists = tk.Frame(root)
        frame_lists.pack(fill=tk.BOTH, expand=True, padx=10)

        frame_dir = tk.Frame(frame_lists)
        frame_dir.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(frame_dir, text="Fitxers a MusicDir:").pack()
        self.listbox_dir = tk.Listbox(frame_dir, selectmode=tk.MULTIPLE)
        self.listbox_dir.pack(fill=tk.BOTH, expand=True)

        frame_rep = tk.Frame(frame_lists)
        frame_rep.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(frame_rep, text="Cua de Reproducció:").pack()
        self.listbox_rep = tk.Listbox(frame_rep)
        self.listbox_rep.pack(fill=tk.BOTH, expand=True)

        frame_btns = tk.Frame(root)
        frame_btns.pack(fill=tk.X, pady=10)

        tk.Button(frame_btns, text="1/2. Afegir al Reproductor", command=self.add).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="3. Eliminar del Reproductor", command=self.remove).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="4. Crear Llista (.m3u)", command=self.create_playlist).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="5. Reproduir", command=self.play, bg="lightgreen").grid(row=1, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="Aturar", command=self.stop, bg="lightcoral").grid(row=2, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="Sortir i Guardar Estat", command=self.exit).grid(row=2, column=1, padx=5, pady=5)

    def set_controller(self, controller):
        self.controller = controller
        self.show_dir()
        self.show_reproductor()

    def show_dir(self):
        self.listbox_dir.delete(0, tk.END)
        for f in os.listdir(MUSIC_DIR):
            if f.endswith('.mp3') or f.endswith('.m3u'):
                self.listbox_dir.insert(tk.END, f)

    def show_reproductor(self):
        self.listbox_rep.delete(0, tk.END)
        for comp in self.controller.reproductor.main_list.components:
            self.listbox_rep.insert(tk.END, comp.name)


    def add(self):
        selected_indices = self.listbox_dir.curselection()
        for idx in selected_indices:
            filename = self.listbox_dir.get(idx)
            if filename.endswith('.mp3'):
                self.controller.add_song(filename)
            elif filename.endswith('.m3u'):
                self.controller.add_playlist(filename)

    def remove(self):
        selected_indices = self.listbox_rep.curselection()
        if selected_indices:
            self.controller.remove_element(selected_indices[0])

    def create_playlist(self):
        selected_indices = self.listbox_dir.curselection()
        if not selected_indices:
            messagebox.showwarning("Avís", "Selecciona fitxers del directori per afegir a la llista.")
            return
        
        name = simpledialog.askstring("Nova Llista", "Introdueix el nom de la llista :")
        if name:
            selected_files = [self.listbox_dir.get(i) for i in selected_indices]
            self.controller.create_playlist(name, selected_files)

    def play(self):
        self.controller.play()

    def stop(self):
        self.controller.stop()

    def exit(self):
        self.controller.exit()

if __name__ == "__main__":
    root = tk.Tk()
    
    reproductor = Reproductor()
    view = View(root)
    controller = Controller(reproductor, view)
    view.set_controller(controller)
    
    root.protocol("WM_DELETE_WINDOW", view.exit)
    root.mainloop()

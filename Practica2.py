# Practica 2
import os
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import json
import tkinter as tk
from tkinter import messagebox, simpledialog
import pygame
from abc import ABC, abstractmethod
import threading

MUSIC_DIR = "MusicDir"
STATE_FILE = "state.json"

if not os.path.exists(MUSIC_DIR):
    os.makedirs(MUSIC_DIR)

pygame.mixer.init()


class MusicComponent(ABC):
    def __init__(self, name:str):
        self._name = name
    @abstractmethod
    def play(self)->None:
        pass
    @abstractmethod
    def stop(self)->None:
        pass
    @abstractmethod
    def show(self)->None:
        pass
    @property
    @abstractmethod
    def length(self)->float:
        pass
    @property
    @abstractmethod
    def elements(self)->list:
        pass
    @property
    @abstractmethod
    def file_name(self)->str:
        pass

class Song(MusicComponent):
    def __init__(self, name:str):
        super().__init__(name)
    def play(self)->None:
        nom_arxiu = '.'.join([self._name, 'mp3'])
        path = os.path.join(MUSIC_DIR, nom_arxiu)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        else:
            print(f"Error: No s'ha trobat el fitxer {nom_arxiu}")
    def stop(self)->None:
        pygame.mixer.music.stop()
    def show(self)->None:
        print(f"{self._name}")
    @property
    def length(self)->float:
        return 1.0
    @property
    def elements(self):
        return [self._name]
    @property
    def file_name(self)->str:
        return '.'.join([self._name, 'mp3'])

class PlayList(MusicComponent):
    # Creem un esdeveniment per quan una canco acaba
    _FINAL_CANCO = pygame.USEREVENT + 1
    pygame.mixer.music.set_endevent(_FINAL_CANCO)

    def __init__(self, name:str):
        super().__init__(name)
        self._components = []
        # Llista de totes les cancos dintre la playlist (descomposant les altres playlist)
        self._a_reproduir = []
        # Indicadors de l'estat de la playlist
        self._reproduint = False
        self._pausat = False
        # Index de la canco que s'esta reproduint (a self._a_reproduir)
        self._index_reproduint = 0

    def play(self)->None:
        # Si ja estem reproduint no fem res
        if (self._reproduint): return
        if (self._pausat): 
            self.resume()
            return
        # Obtenim una llista amb totes les cancons a reproduir
        self._a_reproduir = self.components
        if not self._a_reproduir:
            print("La llista es buida")
            return
        self._reproduint = True
        self._index_reproduint = 0
        self._a_reproduir[self._index_reproduint].play()
        threading.Thread(target=self.song_ended, daemon=True).start()

    def stop(self)->None:
        pygame.mixer.music.stop()
        self._reproduint = False
        self._pausat = False
        self._a_reproduir.clear()
        self._index_reproduint = 0
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def pause(self)->None:
        pygame.mixer.music.pause()
        self._pausat = True

    def resume(self)->None:
        pygame.mixer.music.unpause()
        self._pausat = False

    def song_ended(self):
        while self._reproduint:
            event = pygame.event.wait()
            if event.type == self._FINAL_CANCO:
                self.next()

    def next(self)->None:
        if pygame.mixer.music.get_busy():
            # Parem la canco actual
            pygame.mixer.music.stop()
        self._index_reproduint += 1
        if self._index_reproduint >= len(self._a_reproduir):
            self.stop()
            return
        self._a_reproduir[self._index_reproduint].play()

    def previous(self)->None:
        if pygame.mixer.music.get_busy():
            # Parem la canco actual
            pygame.mixer.music.stop()
        if self._index_reproduint == 0:
            return
        self._index_reproduint -= 1
        self._a_reproduir[self._index_reproduint].play()

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
    @property
    def length(self)->float:
        suma = 0
        for element in self.elements:
            suma += element.length()
        return suma
    @property
    def elements(self):
        elements = []
        for comp in self._components:
            elements.extend(comp.elements())
        return elements
    @property
    def components(self):
        components = []
        for comp in self._components:
            if type(comp) == Song:
                components.extend([comp])
            elif type(comp) == PlayList:
                components.extend(comp.components)
        return components
    @property
    def file_name(self):
        return '.'.join([self._name, 'm3u'])

class Reproductor:
    def __init__(self):
        self._main_list = PlayList("MainList")
        self.update_state()
    def play(self):
        self._main_list.play()

    def stop(self):
        self._main_list.stop()

    def pause(self)->None:
        self._main_list.pause()

    def resume(self)->None:
        self._main_list.resume()

    def next(self)->None:
        self._main_list.next()

    def previous(self)->None:
        self._main_list.previous()

    def add(self, element: MusicComponent)->None:
        self._main_list.Add(element)

    def remove(self, element: MusicComponent)->None:
        self._main_list.remove_element(element)

    def save_state(self)->None:
        files_names = [comp.file_name for comp in self._main_list.components]
        with open(STATE_FILE, 'w') as state_file:
            json.dump(files_names, state_file)
    def update_state(self)->None:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as state_file:
                try:
                    files_names = json.load(state_file)
                    for name in files_names:
                        if name[-4:] == '.mp3':
                            self.add(Song(name))
                        elif name[-4:] == '.m3u':
                            self.add(self.create_playlist_from_file(name))
                except json.JSONDecodeError:
                    pass
    def create_playlist_from_file(self, filename:str)->PlayList:
        # El nom de la playlist es el nom de l'arxiu menys '.m3u'
        pl = PlayList(filename[:-4])
        # El filename passat ja te l'extensio .m3u
        path = os.path.join(MUSIC_DIR, filename)
        # comprovem si existeix l'arxiu i afejim cada element a la llista 
        if os.path.exists(path):
            with open(path, 'r') as pl_file:
                lines = pl_file.read().splitlines()
                for line in lines:
                    if line[-4:] == '.mp3':
                        # Afegim la canço sense l'extensio
                        pl.Add(Song(line[:-4]))
                    elif line[-4:] == '.m3u':
                        pl.Add(self.create_playlist_from_file(line))
        return pl
    @property
    def songs_to_play(self)->list:
        return self._main_list.elements
    @property
    def components_llista(self)->list:
        return self._main_list.components

class Controller:
    def __init__(self, reproductor, view)->None:
        self._reproductor = reproductor
        self._view = view
        
    def add_song(self, song_name:str)->None:
        # Creem la instancia de la canço i l'afegim
        song = Song(song_name)
        self._reproductor.add(song)
        self._view.show_reproductor()

    def add_playlist(self, playlist_name:str)->None:
        # Creem la instancia de la playlist i l'afegim
        pl = self._reproductor.create_playlist_from_file(playlist_name)
        self._reproductor.add(pl)
        self._view.show_reproductor()

    def remove_element(self, index)->None:
        if 0 <= index < len(self._reproductor.main_list.components):
            element = self._reproductor.main_list.components[index]
            self._reproductor.remove(element)
            self._view.show_reproductor()

    def create_playlist(self, name:str, selected_files:list):
        new_pl = PlayList(name)
        for file in selected_files:
            if file[-4:] == '.mp3':
                new_pl.Add(Song(file))
            elif file[-4:] == '.m3u':
                new_pl.Add(self._reproductor.create_playlist_from_file(file))
        new_pl.save_to_file()
        self._view.show_dir()

    def play(self):
        self._reproductor.play()

    def stop(self):
        self._reproductor.stop()

    def pause(self)->None:
        self._reproductor.pause()

    def resume(self)->None:
        self._reproductor.resume()

    def next(self)->None:
        self._reproductor.next()

    def previous(self)->None:
        self._reproductor.previous()

    def exit(self):
        self.stop()
        self._reproductor.save_state()
        self._view.destroy()

    @property
    def components_llista_reproductor(self):
        return self._reproductor.components_llista


class View:
    def __init__(self, root, reproductor:Reproductor):
        self._root = root
        self._root.title("Reproductor de Música - MATCAD")
        self._root.geometry("500x500")
        self._controller = Controller(reproductor, self)

        frame_lists = tk.Frame(self._root)
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

        frame_btns = tk.Frame(self._root)
        frame_btns.pack(fill=tk.X, pady=10)

        tk.Button(frame_btns, text="1/2. Afegir al Reproductor", command=self.add).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="3. Eliminar del Reproductor", command=self.remove).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="4. Crear Llista (.m3u)", command=self.create_playlist).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="5. Play", command=self.play, bg="lightgreen").grid(row=2, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="Stop", command=self.stop, bg="lightcoral").grid(row=2, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="Pausa", command=self.pause).grid(row=3, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="Resume", command=self.resume).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="Seguent", command=self.next).grid(row=4, column=0, padx=5, pady=5)
        tk.Button(frame_btns, text="Anterior", command=self.previous).grid(row=4, column=1, padx=5, pady=5)
        tk.Button(frame_btns, text="Sortir i Guardar Estat", command=self.exit).grid(row=5, column=0, padx=5, pady=5)

    def show_dir(self):
        self.listbox_dir.delete(0, tk.END)
        for f in os.listdir(MUSIC_DIR):
            if f[-4:] == '.mp3' or f[-4:] == '.m3u':
                self.listbox_dir.insert(tk.END, f)

    def show_reproductor(self):
        self.listbox_rep.delete(0, tk.END)
        for comp in self._controller.components_llista_reproductor:
            self.listbox_rep.insert(tk.END, comp.name)


    def add(self):
        selected_indices = self.listbox_dir.curselection()
        for idx in selected_indices:
            filename = self.listbox_dir.get(idx)
            if filename.endswith('.mp3'):
                self._controller.add_song(filename)
            elif filename.endswith('.m3u'):
                self._controller.add_playlist(filename)

    def remove(self):
        selected_indices = self.listbox_rep.curselection()
        if selected_indices:
            self._controller.remove_element(selected_indices[0])

    def create_playlist(self):
        selected_indices = self.listbox_dir.curselection()
        if not selected_indices:
            messagebox.showwarning("Avís", "Selecciona fitxers del directori per afegir a la llista.")
            return
        
        name = simpledialog.askstring("Nova Llista", "Introdueix el nom de la llista :")
        if name:
            selected_files = [self.listbox_dir.get(i) for i in selected_indices]
            self._controller.create_playlist(name, selected_files)

    def play(self)->None:
        self._controller.play()

    def stop(self)->None:
        self._controller.stop()

    def pause(self)->None:
        self._controller.pause()

    def resume(self)->None:
        self._controller.resume()

    def next(self)->None:
        self._controller.next()

    def previous(self)->None:
        self._controller.previous()

    def exit(self)->None:
        self._controller.exit()
    
    def destroy(self)->None:
        self._root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    reproductor = Reproductor()
    view = View(root, reproductor)
    
    root.protocol("WM_DELETE_WINDOW", view.exit)
    root.mainloop()

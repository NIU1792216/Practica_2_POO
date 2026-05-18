# Diagramas de secuencia de los casos de uso
## Caso 1
@startuml
actor Usuari
participant "View" as V
participant "Controller" as C
participant "Reproductor" as R
participant "main_list: PlayList" as PL

Usuari -> V : Selecciona cançó (.mp3)
V -> C : add(song: Song)
C -> R : add(song)
R -> PL : Add(song)
@enduml

## Caso 2
@startuml

actor Usuari
participant "View" as V
participant "Controller" as C
participant "Reproductor" as R
participant "main_list: PlayList" as PL

Usuari -> V : Selecciona llista (.m3u)
V -> C : add(playlist: PlayList)
C -> R : add(playlist)
R -> PL : Add(playlist)
@enduml

## Caso 3
@startuml

actor Usuari
participant "View" as V
participant "Controller" as C
participant "Reproductor" as R
participant "main_list: PlayList" as PL

Usuari -> V : Selecciona element a eliminar
V -> C : remove(element: MusicComponent)
C -> R : remove(element)
R -> PL : remove_element(element)
@enduml

## Caso 4
@startuml
actor Client as cl
participant "v:View" as v
participant "c:Controller" as c
participant "l:PlayLlist" as l

cl -> v : create_PlayList()
v --> l : <<create>>
l --> l.m3u : <<create>>
l --> l.txt : <<create>>

cl -> v : add(s:Song)
v -> c : add(s:Song)
c -> l : add(s:Song)
l -> l.m3u : append(s:Song)
l -> "s:Song" : get_name()
"s:Song" --> l : s_name
l -> l.txt : append("s_name.mp3")

cl -> v : add(l2:Playlist)
v -> c : add(l2:PlayList)
c -> l : add(l2:PlayList)
l -> l.m3u : append(l2:PlayList)
l -> "l2:PlayList" : get_name()
"l2:PlayList" --> l : l2_name
l -> l.txt : append("l2_name.m3u")
@enduml

## Caso 5
@startuml
actor Client as cl
participant "v:View" as v
participant "c:Controller" as c
participant "r:Reproductor" as r
participant "main_list:PlayList" as ml
participant "l1:PlayLlist" as l1
participant "s1:Song" as s

cl -> v : play()
v -> c : play()
c -> r : play()
r -> ml : play()
loop for each MusicElement in self.elements
    ml -> l1 : play()
    l1 --> ml
    ml -> s1 : play()
    s1 --> ml
end

@enduml

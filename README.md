### Repozytorium łączące projekty - imutils, ball_follower_python, BallFollower, docker scriprs

Opis:
- imutils - fork projektu imutils z dodaną obsługą kamery Raspbery Pi camera v2 na platformie Nvidia Jetson Nano, z wykorzystaniem GStreamer pipeline. W celu instalacji należy wejść do katalogu i wykonać polecenie: "pip3 install --upgrade ."
- ball_follower - kod przykładowy umożliwiający śledzenie obiektu o wybranym kolorze. Należy traktować jako quickstart pokazujący możliwości a nie rozwiązanie docelowe
- BallFollower - projekt w formacie PlatformIO (VS Code) zawierający kod wykonywany na mikrokontrolerze teensy
- [deprecated] docker_scripts - skrypty umożliwiające uruchomienie narzędzia docker z dostępem do kamery Raspberry Pi Camera v2 oraz GPU, programowanie z wykorzystaniem narzędzie JupyterLab (w przeglądarce)
- Sensors - kod przykładowy, wykonywany na Teensy, do obsługi czujników ultradźwiękowych oraz enkoderów na kołach
- AI - przykład kodu uruchamiającego wytrenowany model SSD-Mobilenet w formacie ONNX
- VideoGrabber - kod umożliwiający pobranie obrazu z kamery autka i zapisanie na dysku (do późniejszej analizy)
- RemoteControl - kod umożliwiający zdalne sterowanie platformą z pomocą gamepada, w oparciu o websockets (!rozwiązanie pokazowe, nie do użytku produkcyjnego!)
- RemoteControlTeensy - projekt w formacie PlatformIO (VS Code) zawierający kod wykonywany na mikrokontrolerze teensy (sterowanie)
- RemoteImShow - kod umożliwiający wysyłanie obrazu z platformy na serwer zewnętrzny, w oparciu o websockets (!rozwiązanie pokazowe, nie do użytku produkcyjnego!)
- CameraTest - proste skrypty prezentujące dostęp do kamery z wykorzystaniem zmodyfikowanej biblioteki imutils oraz jetson.utils




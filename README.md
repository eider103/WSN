# Red de sensores inalámbrica (WSN)
El repositorio recoge los códigos de mis contribuciones en el proyecto de **red de sensores inalámbrica (WSN)**, realizado en el **Máster en Microelectrónica de la UPV/EHU**.  

## 🔬📊 Descripción del proyecto

Este proyecto consistió en una red de sensores, físicamente distribuídos, con el objetivo de monitorizar una sala blanca. Los sensores, conectados a microcontroladores ESP32-S3, envían los datos recogidos por WiFi. Se implementa el protocolo MQTT para la comunicación (en un contenedor Docker) y se desarrolla una GUI que permite la visualización de los datos a tiempo real e histórico.

Se escogieron sensores para monitorizar las siguientes magnitudes: temperatura, humedad, presión, CO2, parículas en suspensión, espectro de luz, masa de objetos, constante dieléctrica (traducida a espesor) de FR4 y acceso.

## 🔍 Contenido del repositorio
  * Código de programación del sensor de control de acceso RFID RC522 en el entorno Arduino (C++)
  * GUI que, conectado a VNA con sensor RF, determina el espesor de FR4 mediante el desfase de S11

## 👩‍🎓 Autoría

**Eider Sanchez Nuin**  
GitHub: [eider103](https://github.com/eider103)  
Contacto: [esanchez103@ikasle.ehu.eus](mailto:esanchez103@ikasle.ehu.eus)

**Institución:**
Facultad de Ciencia y Tecnología (UPV/EHU)

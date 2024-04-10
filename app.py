import os, socket, sys, time, xml.etree.ElementTree

ADDRESS = sys.argv[1]
PORT = int(sys.argv[2])

SERVICES = (
    'alarmserver_multi',
    'alarmserver_x1',
    'alarmserver_x2',
    'extractor_tracker_x1',
    'extractor_tracker_x2',
    'in_proxy_targetmanager_multi',
    'in_proxy_x1',
    'NMEAsupervisor_multi',
    'NMEAsupervisor_x1',
    'NMEAsupervisor_x2',
    'radarserver_x1',
    'radarserver_x2',
    'snmp_manager',
    'targetmanager_multi',
    'targetmanager_x1',
    'targetmanager_x2'
)

CONNECTED = False

while not CONNECTED:

    try:
        TS = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        TS.connect((ADDRESS, PORT))
        print(f"Connected with TS @ {ADDRESS}:{PORT}")
        CONNECTED = True
        
    except:
        print(f"Connection with TS @ {ADDRESS}:{PORT} failed, retrying...")
        time.sleep(1)
        CONNECTED = False

while True:

    data = TS.recv(999999999)
    
    if data != b'<prefab/>\r\n':
    
        root = xml.etree.ElementTree.fromstring(data.decode())
        info = root[0]
        elements = root[1]
        
        for child in info.findall('code'): code = child.text
        for child in info.findall('name'): name = child.text
        for child in info.findall('length'): length = float(child.text)
        for child in info.findall('width'): width = float(child.text)
        
        print(f"Assigned to {code} ({name}) as {elements[0][0].text}")
        
        for child in elements.iter('element'):
        
            if child.attrib['group'] == "Sensors" and child.attrib['type'] == "Sensors::DGPS":
                dgps = child[1].text.split(",")
                dgpsx = float(dgps[0])
                dgpsy = float(dgps[1])
                dgpsz = float(dgps[2])
                dist_to_bow = length / 2 - dgpsy
                dist_to_stern = length - dist_to_bow
                dist_to_larboard = width / 2 - dgpsx
                dist_to_starboard = width - dist_to_larboard
                
            if child.attrib['group'] == "Sensors" and child.attrib['type'] == "Sensors::Radar":

                radar_name = child[0].text.lower().replace(" ", "")

                if radar_name == "radar" or radar_name == "radar1" or radar_name == "radarx-band":
                    single_radar = True
                    radar1 = child[1].text.split(",")
                    radar1x = float(radar1[0]) - dgpsx
                    radar1y = float(radar1[1]) - dgpsy
                    radar1z = float(radar1[2]) - dgpsz
                        
                if radar_name == "radar2" or radar_name == "radars-band":
                    single_radar = False
                    radar2 = child[1].text.split(",")
                    radar2x = float(radar2[0]) - dgpsx
                    radar2y = float(radar2[1]) - dgpsy
                    radar2z = float(radar2[2]) - dgpsz
        
        DIRECTORIES=(
            'C:/ProgramData/innovative-navigation/config/imRADAR',
            'C:/ProgramData/innovative-navigation/config/targetmanager_multi',
            'C:/ProgramData/innovative-navigation/config/targetmanager_x1',
            'C:/ProgramData/innovative-navigation/config/targetmanager_x2',
            'C:/ProgramData/innovative-navigation/config/common'
        )

        for directory in DIRECTORIES:
            print(f"Writing own_ship.config file in directory {directory}")
            with open(f'{directory}/own_ship.config', 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n')
                f.write('<!DOCTYPE xml>\n')
                f.write('<xml>\n')
                f.write('\t<own_ship>\n')
                f.write(f'\t\t<dist_to_bow>{dist_to_bow}</dist_to_bow>\n')
                f.write(f'\t\t<dist_to_stern>{dist_to_stern}</dist_to_stern>\n')
                f.write(f'\t\t<dist_to_larboard>{dist_to_larboard}</dist_to_larboard>\n')
                f.write(f'\t\t<dist_to_starboard>{dist_to_starboard}</dist_to_starboard>\n')
                f.write('\t\t<equipment>\n')
                f.write('\t\t\t<type>radar</type>\n')
                f.write('\t\t\t<id>XBand</id>\n')
                f.write(f'\t\t\t<x>{radar1x}</x>\n')
                f.write(f'\t\t\t<y>{radar1y}</y>\n')
                f.write(f'\t\t\t<z>{radar1z}</z>\n')
                f.write('\t\t\t<coverage>tracking_coverage_x1.config</coverage>\n')
                f.write('\t\t</equipment>\n')
                if not single_radar:
                    f.write('\t\t<equipment>\n')
                    f.write('\t\t\t<type>radar</type>\n')
                    f.write('\t\t\t<id>SBand</id>\n')
                    f.write(f'\t\t\t<x>{radar2x}</x>\n')
                    f.write(f'\t\t\t<y>{radar2y}</y>\n')
                    f.write(f'\t\t\t<z>{radar2z}</z>\n')
                    f.write('\t\t\t<coverage>tracking_coverage_x2.config</coverage>\n')
                    f.write('\t\t</equipment>\n')
                f.write('\t</own_ship>\n')
                f.write('</xml>')
            f.close()
        
        for service in SERVICES:
            print(f"Starting service: {service}")
            os.system(f"sc start {service} >nul")
        
        print("Stopping imRADAR.exe to reload own_ship.config") # Watchdog will restart imRADAR.exe
        os.system("TASKKILL /F /IM imRADAR.exe >nul")

    else:
    
        print("Unassigned")
        
        for service in SERVICES:
            print(f"Stopping service: {service}")
            os.system(f"sc stop {service} >nul")

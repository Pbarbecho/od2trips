import os, glob, sys
import multiprocessing
from utils import create_folder, SUMO_outputs_process, simulate, gen_sumo_cfg, exec_od2trips, gen_od2trips, create_O_file
from duaiterate import exec_DUAIterate


# SUMO environment variable
if 'SUMO_HOME' in os.environ:
    sumo_env_var = os.getenv('SUMO_HOME')
    sumo_exec = os.path.join(sumo_env_var, 'bin')
    sumo_tools = os.path.join(sumo_env_var, 'tools')
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


class General_configs:
     def __init__(self):
        # initial configurations
        self.parents_dir = os.path.dirname(os.path.abspath('{}/'.format(__file__)))
        self.outputs = os.path.join(self.parents_dir,'outputs')
        self.tool = '' # creates the output file according to the selected tool (randomtrip, od2)
        self.map_folder = os.path.join(self.parents_dir,'map') # location of traffic csv file
        self.taz_file = ''
        self.realtraffic =''

        # OD2Trips Variables
        self.current_origen_district = ''  # temp variable for iterate over Origin districts
        self.current_destination_district = ''  # temp variable for iterate over destination districts
        self.O_file_temp_name = ''
        self.od2_end_hour = 1
        self.od2_multiplicative_factor = 1
        self.od2_repetitions = 1

        #Duaiterate
        self.dua_network_update = 60 # secs

        self.html = ''
        self.factor = 1
        self.run_command = ''
        self.rou_dir = ''
        self.sumo_cfg_dir = ''
        self.isCommandExecutionSuccessful = False

        self.simtime = 1
        self.repetitions = 1

        self.O_district = ''
        self.D_district = ''
        self.processors = multiprocessing.cpu_count()
        # SUMO variables
        self.SUMO_exec = sumo_exec
        self.SUMO_tool = sumo_tools
        self.SUMO_outputs = ''

        self.net_folder_var = self.parents_dir
        self.trips = ''


        self.O = ''
        self.dua = ''
        self.duai = ''
        self.ma = ''
        self.cfg = ''
        self.detector = ''
        self.xmltocsv = ''
        self.parsed = ''
        self.reroute = ''
        self.edges = ''
        self.reroute_probability = 0
        self.sumo_var_tripinfo = True
        self.sumo_var_emissions = True
        self.sumo_var_summary = True
        self.sumo_var_gui = False
        self.routing = ''
        self.osm = ''
        self.network = ''
        self.poly = ''
        self.rou_file = ''
        self.ev_penetration = 0  # used in randomtrips
        self.duaiterations = 5  # default


def create_SUMO_folders(self):
    self.SUMO_outputs = os.path.join(self.parents_dir, 'outputs')
    if not os.path.lexists(self.SUMO_outputs): os.makedirs(self.SUMO_outputs)
    self.SUMO_tool = os.path.join(self.SUMO_outputs, self.tool)
    create_folder(self.SUMO_tool)
    subfolders = ['html', 'trips', 'O', 'dua', 'ma', 'cfg', 'outputs', 'detector', 'xmltocsv', 'parsed', 'reroute',
                  'edges', 'duaiterate']
    # create subfolders
    for sf in subfolders: create_folder(os.path.join(self.SUMO_tool, sf))
        # update subfolders paths
    self.trips = os.path.join(self.SUMO_tool, 'trips')
    self.O = os.path.join(self.SUMO_tool, 'O')
    self.dua = os.path.join(self.SUMO_tool, 'dua')
    self.duai = os.path.join(self.SUMO_tool, 'duai')
    self.ma = os.path.join(self.SUMO_tool, 'ma')
    self.cfg = os.path.join(self.SUMO_tool, 'cfg')
    self.outputs = os.path.join(self.SUMO_tool, 'outputs')
    self.detector = os.path.join(self.SUMO_tool, 'detector')
    self.xmltocsv = os.path.join(self.SUMO_tool, 'xmltocsv')
    self.parsed = os.path.join(self.SUMO_tool, 'parsed')
    self.reroute = os.path.join(self.SUMO_tool, 'reroute')
    self.edges = os.path.join(self.SUMO_tool, 'edges')
    self.html = os.path.join(self.SUMO_tool, 'html')
    self.plots = os.path.join(self.SUMO_tool, 'plots')



def clean_folder(folder):
    files = glob.glob(os.path.join(folder, '*'))
    [os.remove(f) for f in files]
    # print(f'Cleanned: {folder}')


def gen_routes(O, k, configurations, gen_sumocfg_file):
    """
    Generate configuration files for od2 trips
    """
    output_name = ''

    if configurations.tool == 'od2':
        # Generate XML od2trips cfg file
        cfg_name, output_name = gen_od2trips(O, k, configurations)

        # Execute XML od2trips cfg file
        output_name = exec_od2trips(cfg_name, output_name, configurations)

        # Generate sumo cfg
        if gen_sumocfg_file:
            gen_sumo_cfg(configurations,k,output_name)  # last element reroute probability

    else:
        SystemExit(f'Routing Tool {configurations.tool} not found')

    return output_name


def exec_duarouter_cmd(fname):
    print('\nRouting  .......')
    cmd = f'duarouter -c {fname}'
    os.system(cmd)


def exec_marouter_cmd(fname):
    print('\nRouting  .......')
    cmd = f'marouter -c {fname}'
    os.system(cmd)


def gen_route_files(configurations, gen_sumocfg_file):
    # generate cfg files
    for origin in [configurations.O_district]:
        for destination in [configurations.D_district]:
            configurations.current_origen_district = origin
            configurations.current_destination_district = origin

            # Build O file
            O_name = os.path.join(configurations.O, f'{origin}_{destination}') #filename
            configurations.O_file_temp_name = O_name # update current O file name

            # Create an O/D file for each hour
            create_O_file(configurations)

            # Generate cfg files
            for k in range(configurations.od2_repetitions):
                # backup O files
                O_files = os.listdir(configurations.O)
                # Gen Od2trips
                cfg_file_loc = gen_routes(O_name, k, configurations,gen_sumocfg_file)
    return cfg_file_loc


def od2(config, k, repetitions, end_hour, processors, routing, gui):
    # Generate configurtion files
    gen_route_files(config, k, repetitions, end_hour, routing)
    # Execute OD@Trips simulations
    #simulate(config, processors, gui)
    # Outputs preprocess
    #SUMO_outputs_process(config)

####################################
###########  OD2TRIPS ###############
####################################
#1. Generating O/D files for given TAZ:
#2. Create XML OD2Trips cfg file:
#3. Execute XML OD2Trips cfg file (SUMO od2trip tool):
#4. Remove "fromTaz=" "toTaz=" entry and create files copy:
####################################

# Instantiate General Configurations
configurations = General_configs()

# Create output folders
configurations.tool = 'od2'
create_SUMO_folders(configurations)

# Set TAZ names and traffic file name
configurations.O_district = 'taz_0'
configurations.D_district = 'taz_1'
configurations.taz_file = os.path.join(configurations.map_folder, 'TAZ.xml')
configurations.realtraffic = os.path.join(configurations.map_folder, 'traffic_file.csv') #file name. Notice that the traffic file is located inside the map folder

# Set O/D parameters
configurations.od2_end_hour = 3

#Generate OD2TRIPS files with SUMO OD2Trips tool
od2trips_file = gen_route_files(configurations, False) # gen_sumocfg_file = False

####################################
###########  DUAITERATE ############
####################################
#5. Generating O/D files for given TAZ:
####################################
configurations.network = os.path.join(configurations.map_folder,'osm.net.xml')
configurations.duaiterations = 5 # number of duaiterations
configurations.dua_network_update = 120 # seconds to update network status during duaiterate process

# Execute duaiterate tool with OD2trips trips input
route_file_last_iter = exec_DUAIterate(configurations, od2trips_file)
# generate sumo cfg with the new rou file
#gen_sumo_cfg(route_file_last_iter, k, config)  # last element reroute probability



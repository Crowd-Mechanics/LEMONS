/*
    Copyright  2025  Institute of Light and Matter, CNRS UMR 5306, University Claude Bernard Lyon 1
    Contributors: Oscar DUFOUR, Maxime STAPELLE, Alexandre NICOLAS

    This software is a computer program designed to generate a realistic crowd from anthropometric data and
    simulate the mechanical interactions that occur within it and with obstacles.

    This software is governed by the CeCILL-B license under French law and abiding by the rules of distribution
    of free software.  You can  use, modify and/ or redistribute the software under the terms of the CeCILL-B
    license as circulated by CEA, CNRS and INRIA at the following URL "http://www.cecill.info".

    As a counterpart to the access to the source code and  rights to copy, modify and redistribute granted by
    the license, users are provided only with a limited warranty  and the software's author,  the holder of the
    economic rights,  and the successive licensors  have only  limited liability.

    In this respect, the user's attention is drawn to the risks associated with loading,  using,  modifying
    and/or developing or reproducing the software by the user in light of its specific status of free software,
    that may mean  that it is complicated to manipulate,  and  that  also therefore means  that it is reserved
    for developers  and  experienced professionals having in-depth computer knowledge. Users are therefore
    encouraged to load and test the software's suitability as regards their requirements in conditions enabling
    the security of their systems and/or data to be ensured and,  more generally, to use and operate it in the
    same conditions as regards security.

    The fact that you are presently reading this means that you have had knowledge of the CeCILL-B license and that
    you accept its terms.
*/

#include <map>
#include <string>
#include <vector>

#include "CrowdMechanics.h"

using std::string, std::map, std::vector;

//  extern C is a trick for Python ctypes to work
extern "C"
{
    /**
     * @brief The main function of CrowdMechanics, and the only one to be called when used as a library.
     *
     * It reads static and dynamic XML files,
     * stores everything and simulates the dynamics of the agents.
     *
     * @param files An array of file names. They should be given in a precise order:
     *      - Parameters (directories, time step...)
     *      - Materials (with Young's modulus and the shear modulus
     *      - Geometry (obstacles)
     *      - Agents
     *      - Agent dynamics (current kinematics, and driving forces and torques)
     *      - (optional) Agent interactions (the information about agent-to-agent and agent-to-obstacle contacts,
     *                   if any, will be used.
     *
     * @return  EXIT_SUCCESS if the program executed successfully.
     *          EXIT_FAILURE in case of issue(s) with any of the XML files' contents
     */
    int CrowdMechanics(char** files)
    {
        /*  Read general PARAMETERS  */
        if (const string parametersFile = files[0]; readParameters(parametersFile) == EXIT_FAILURE)
            return EXIT_FAILURE;
        //  Store the dynamics file name, whether it is the first run or not
        const string dynamicsFile = pathDynamic + files[4];

        if (loadStaticData)
        {
            /*  Read MATERIALS  */
            //  Mapping between user-given id's and indexes in the program
            map<string, int32_t> materialMapping;
            if (const string materialsFile = pathStatic + files[1]; readMaterials(materialsFile, materialMapping) == EXIT_FAILURE)
                return EXIT_FAILURE;

            /*  Read GEOMETRY   */
            if (const string geometryFile = pathStatic + files[2]; readGeometry(geometryFile, materialMapping) == EXIT_FAILURE)
                return EXIT_FAILURE;

            /*  Read AGENTS */
            vector<unsigned> nb_shapes_allagents, shapeIDagent;
            vector<int> edges;
            vector<double> radius_allshapes, masses, mois;
            vector<double2> delta_gtos;
            if (const string agentsFile = pathStatic + files[3];
                readAgents(agentsFile, nb_shapes_allagents, shapeIDagent, edges, radius_allshapes, masses, mois, delta_gtos,
                           materialMapping) == EXIT_FAILURE)
                return EXIT_FAILURE;

            /*  Initialise simulation  */
            if (initialiseSetting(dynamicsFile, nb_shapes_allagents, shapeIDagent, edges, radius_allshapes, masses, mois,
                                  delta_gtos) == EXIT_FAILURE)
                return EXIT_FAILURE;
        }
        else if (updateSetting(dynamicsFile) == EXIT_FAILURE)
            return EXIT_FAILURE;

        /*  Main program procedure  */
        handleMechanicalLayer(dynamicsFile);

        loadStaticData = false;
        return EXIT_SUCCESS;
    }
}

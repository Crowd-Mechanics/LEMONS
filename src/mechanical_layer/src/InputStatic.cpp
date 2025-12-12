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

#include "InputStatic.h"

#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "../3rdparty/tinyxml/tinyxml2.h"

using std::cout, std::cerr, std::string, std::endl, std::vector, std::map;

/**
 * @brief Reads the Parameters XML file.
 *
 * @param file The name of the file
 *
 * @return EXIT_FAILURE in case of issue in the XML file (missing or unreadable field)
 *         EXIT_SUCCESS otherwise
 */
int readParameters(const std::string& file)
{
    tinyxml2::XMLDocument document;
    document.LoadFile(file.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse Parameters file " << file << endl;
        return EXIT_FAILURE;
    }
    /*  Read the Parameters block */
    tinyxml2::XMLElement* parametersElement = document.FirstChildElement("Parameters");
    if (!parametersElement)
    {
        cerr << "Error: Parameters must be embedded in \"Parameters\" tag!" << endl;
        return EXIT_FAILURE;
    }
    /*  Read times */
    const tinyxml2::XMLElement* timesElement = parametersElement->FirstChildElement("Times");
    if (!timesElement)
    {
        cerr << "Error: no Times present in " << file << endl;
        return EXIT_FAILURE;
    }
    if (timesElement->QueryDoubleAttribute("TimeStep", &dt) != tinyxml2::XML_SUCCESS)
    {
        cerr << R"(Error: Could not read "TimeStep" attribute in )" << file << endl;
        return EXIT_FAILURE;
    }
    if (timesElement->QueryDoubleAttribute("TimeStepMechanical", &dt_mech) != tinyxml2::XML_SUCCESS)
    {
        cerr << R"(Error: Could not read "TimeStepMechanical" attribute in )" << file << endl;
        return EXIT_FAILURE;
    }
    /*  Input and Output directories    */
    const char *staticDirectory, *dynamicDirectory;
    if (const tinyxml2::XMLElement* directoriesElement = parametersElement->FirstChildElement("Directories"))
    {
        if (directoriesElement->QueryStringAttribute("Static", &staticDirectory) != tinyxml2::XML_SUCCESS)
        {
            cerr << R"(Error: Could not read the directory for "static" files in )" << file << endl;
            return EXIT_FAILURE;
        }
        if (directoriesElement->QueryStringAttribute("Dynamic", &dynamicDirectory) != tinyxml2::XML_SUCCESS)
        {
            cerr << R"(Error: Could not read the directory for "dynamic" files in )" << file << endl;
            return EXIT_FAILURE;
        }
        pathStatic = staticDirectory;
        pathDynamic = dynamicDirectory;
    }

    return EXIT_SUCCESS;
}
/**
 * @brief Reads the Materials XML file.
 *
 * @param file The name of the file
 * @param materialMapping The mapping of user-provided material ids and our internal id
 *
 * @return EXIT_FAILURE in case of issue in the XML file (missing or unreadable field)
 *         EXIT_SUCCESS otherwise
 */
int readMaterials(const std::string& file, std::map<std::string, int32_t>& materialMapping)
{
    //  If the library is called from many runs where the user forces firstRun=True because of changed static
    //  data, we first clear the global variables
    if (intrinsicProperties)
    {
        delete intrinsicProperties[YOUNG_MODULUS];
        delete intrinsicProperties[SHEAR_MODULUS];
        intrinsicProperties = nullptr;
        for (uint8_t n = 0; n < nBinaryProperties; n++)
        {
            for (uint32_t m = 0; m < nMaterials; m++)
            {
                delete binaryProperties[n][m];
                binaryProperties[n][m] = nullptr;
            }
            delete binaryProperties[n];
            binaryProperties[n] = nullptr;
        }
    }
    tinyxml2::XMLDocument document;
    document.LoadFile(file.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse XML file " << file << endl;
        return EXIT_FAILURE;
    }

    /*  Read the Materials block */
    tinyxml2::XMLElement* materialsElement = document.FirstChildElement("Materials");
    if (!materialsElement)
    {
        cerr << "Error: Information about materials must be embedded in \"Materials\" tag!" << endl;
        return EXIT_FAILURE;
    }

    /*  Read intrinsic properties */
    const tinyxml2::XMLElement* intrinsicElement = materialsElement->FirstChildElement("Intrinsic");
    if (!intrinsicElement)
    {
        cerr << "Error: no Intrinsic tag present in " << file << endl;
        return EXIT_FAILURE;
    }
    //  Materials
    vector<double2> elasticProperties;
    const tinyxml2::XMLElement* materialElement = intrinsicElement->FirstChildElement("Material");
    if (!materialElement)
    {
        cerr << "Error: no materials in " << file << endl;
        return EXIT_FAILURE;
    }
    vector<string> materialIds;
    nMaterials = 0;
    while (materialElement)
    {
        const char* id = nullptr;
        if (materialElement->QueryStringAttribute("Id", &id) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: found material with no id in " << file << endl;
            return EXIT_FAILURE;
        }
        materialMapping[id] = static_cast<int32_t>(nMaterials);
        double E, G;
        if (materialElement->QueryDoubleAttribute("YoungModulus", &E) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error for material id " << id << ": Young's modulus (E) not provided!" << endl;
            return EXIT_FAILURE;
        }
        if (materialElement->QueryDoubleAttribute("ShearModulus", &G) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error for material id " << id << ": Shear modulus (G) not provided!" << endl;
            return EXIT_FAILURE;
        }
        elasticProperties.emplace_back(E, G);
        materialIds.emplace_back(static_cast<string>(id));
        nMaterials++;

        materialElement = materialElement->NextSiblingElement("Material");
    }
    /*  Allocate global variables, now that we know the materials   */
    intrinsicProperties = new double*[nIntrinsicProperties];
    for (uint32_t i = 0; i < nIntrinsicProperties; i++)
    {
        intrinsicProperties[i] = new double[nMaterials];
    }
    binaryProperties = new double**[nBinaryProperties];
    for (uint32_t i = 0; i < nBinaryProperties; i++)
    {
        binaryProperties[i] = new double*[nMaterials];
        for (uint32_t j = 0; j < nMaterials; j++)
        {
            binaryProperties[i][j] = new double[nMaterials];
        }
    }
    /*  Populate intrinsic parameters   */
    for (uint32_t i = 0; i < nMaterials; i++)
    {
        intrinsicProperties[YOUNG_MODULUS][i] = elasticProperties[i].first;
        intrinsicProperties[SHEAR_MODULUS][i] = elasticProperties[i].second;
    }
    /*  Populate binary parameters  */
    //  Find stiffness combinations from intrinsic properties
    for (uint32_t i = 0; i < nMaterials; i++)
    {
        for (uint32_t j = 0; j < nMaterials; j++)
        {
            double stiffnessNormal = computeStiffnessNormal(i, j);
            if (stiffnessNormal <= 0)
            {
                cerr << "Error: materials '" << materialIds[i] << "' and '" << materialIds[j]
                     << "' produce non positive normal stiffness!" << endl;
                return EXIT_FAILURE;
            }
            binaryProperties[STIFFNESS_NORMAL][j][i] = stiffnessNormal;
            binaryProperties[STIFFNESS_NORMAL][i][j] = stiffnessNormal;
            double stiffnessTangential = computeStiffnessTangential(i, j);
            if (stiffnessTangential <= 0)
            {
                cerr << "Error: materials '" << materialIds[i] << "' and '" << materialIds[j]
                     << "' produce non positive tangential stiffness!" << endl;
                return EXIT_FAILURE;
            }
            binaryProperties[STIFFNESS_TANGENTIAL][j][i] = stiffnessTangential;
            binaryProperties[STIFFNESS_TANGENTIAL][i][j] = stiffnessTangential;
        }
    }
    //  Read the rest of the binary properties from the XML file - <Binary>
    const tinyxml2::XMLElement* relationshipsElement = materialsElement->FirstChildElement("Binary");
    if (!relationshipsElement)
    {
        cerr << "Error: no Binary tag present in " << file << endl;
        return EXIT_FAILURE;
    }
    const tinyxml2::XMLElement* relationshipElement = relationshipsElement->FirstChildElement("Contact");
    if (!relationshipElement)
    {
        cerr << "Error: no binary properties at all in " << file << endl;
        return EXIT_FAILURE;
    }
    while (relationshipElement)
    {
        const char* id1 = nullptr;
        const char* id2 = nullptr;
        if (relationshipElement->QueryStringAttribute("Id1", &id1) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: no Id1 in binary property in " << file << endl;
            return EXIT_FAILURE;
        }
        if (relationshipElement->QueryStringAttribute("Id2", &id2) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: no Id2 in binary property in " << file << endl;
            return EXIT_FAILURE;
        }
        if (!materialMapping.contains(id1) || !materialMapping.contains(id2))
        {
            cerr << "Error: relationships include unknown material ids " << id1 << "or " << id2 << "." << endl;
            return EXIT_FAILURE;
        }
        double gamma_n, gamma_t, mu_d;
        if (relationshipElement->QueryDoubleAttribute("GammaNormal", &gamma_n) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error for material ids " << id1 << "-" << id2 << ": normal damping (GammaNormal) not provided!" << endl;
            return EXIT_FAILURE;
        }
        if (relationshipElement->QueryDoubleAttribute("GammaTangential", &gamma_t) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error for material ids " << id1 << "-" << id2 << ": tangential damping (GammaTangential) not provided!" << endl;
            return EXIT_FAILURE;
        }
        if (relationshipElement->QueryDoubleAttribute("KineticFriction", &mu_d) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error for material ids " << id1 << "-" << id2 << ": kinetic friction (KineticFriction) not provided!" << endl;
            return EXIT_FAILURE;
        }
        //  Fill the remaining slots in the symmetric binaryProperties matrix
        binaryProperties[DAMPING_NORMAL][materialMapping[id1]][materialMapping[id2]] = gamma_n;
        binaryProperties[DAMPING_NORMAL][materialMapping[id2]][materialMapping[id1]] = gamma_n;
        binaryProperties[DAMPING_TANGENTIAL][materialMapping[id1]][materialMapping[id2]] = gamma_t;
        binaryProperties[DAMPING_TANGENTIAL][materialMapping[id2]][materialMapping[id1]] = gamma_t;
        binaryProperties[FRICTION_SLIDING][materialMapping[id1]][materialMapping[id2]] = mu_d;
        binaryProperties[FRICTION_SLIDING][materialMapping[id2]][materialMapping[id1]] = mu_d;
        relationshipElement = relationshipElement->NextSiblingElement("Contact");
    }

    return EXIT_SUCCESS;
}
/**
 * @brief Reads the Geometry XML file.
 *
 * @param file The name of the file
 * @param materialMapping The known mapping between user-provided material ids and our ids for them
 *
 * @return EXIT_FAILURE in case of issue in the XML file (missing or unreadable field)
 *         EXIT_SUCCESS otherwise
 */
int readGeometry(const std::string& file, std::map<std::string, int32_t>& materialMapping)
{
    //  If the library is called from many runs where the user forces firstRun=True because of changed static
    //  data, we first clear the global variables
    if (!listObstacles.empty())
    {
        listObstacles.clear();
        obstaclesMaterial.clear();
    }
    tinyxml2::XMLDocument document;
    document.LoadFile(file.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse XML file " << file << endl;
        return EXIT_FAILURE;
    }

    /*  Read the Geometry block */
    tinyxml2::XMLElement* geometryElement = document.FirstChildElement("Geometry");
    if (!geometryElement)
    {
        cerr << "Error: Information about geometry must be embedded in \"Geometry\" tag!" << endl;
        return EXIT_FAILURE;
    }

    /*  Read dimensions */
    const tinyxml2::XMLElement* dimensionsElement = geometryElement->FirstChildElement("Dimensions");
    if (!dimensionsElement)
    {
        cerr << "Error: no Dimensions tag present in " << file << endl;
        return EXIT_FAILURE;
    }
    if (dimensionsElement->QueryDoubleAttribute("Lx", &Lx) != tinyxml2::XML_SUCCESS)
    {
        cerr << "Error: Could not parse domain dimensions from XML file " << file << endl;
        return EXIT_FAILURE;
    }
    if (dimensionsElement->QueryDoubleAttribute("Ly", &Ly) != tinyxml2::XML_SUCCESS)
    {
        cerr << "Error: Could not parse domain dimensions from XML file " << file << endl;
        return EXIT_FAILURE;
    }

    /*  Read Walls  */
    const tinyxml2::XMLElement* wallElement = geometryElement->FirstChildElement("Wall");
    if (!wallElement)
    {
        cerr << "Error: no wall present on geometry file " << file << endl;
        return EXIT_FAILURE;
    }
    while (wallElement != nullptr)
    {
        //  Fetch material
        const char* materialId = nullptr;
        if (wallElement->QueryStringAttribute("MaterialId", &materialId) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: no material mentioned for wall on geometry file " << file << endl;
            return EXIT_FAILURE;
        }
        if (!materialId || !materialMapping.contains(materialId))
        {
            cerr << "Error: unknown or absent material id " << materialId << " given for one of the walls" << endl;
            return EXIT_FAILURE;
        }
        else
            obstaclesMaterial.push_back(materialMapping[materialId]);

        vector<double2> wall;
        const tinyxml2::XMLElement* cornerElement = wallElement->FirstChildElement("Corner");
        if (!cornerElement)
        {
            cerr << "Error: no corners in wall!" << endl;
            return EXIT_FAILURE;
        }
        while (cornerElement != nullptr)
        {
            const char* buffer = nullptr;
            if (cornerElement->QueryStringAttribute("Coordinates", &buffer) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: Could not parse corner coordinates from XML file " << file << endl;
                return EXIT_FAILURE;
            }
            auto [rc, coordinates] = parse2DComponents(buffer);
            if (rc != EXIT_SUCCESS)
            {
                cerr << "Error: Could not parse corner coordinates from XML file " << file << endl;
                return EXIT_FAILURE;
            }
            wall.emplace_back(coordinates);
            cornerElement = cornerElement->NextSiblingElement("Corner");
        }
        listObstacles.push_back(wall);

        wallElement = wallElement->NextSiblingElement("Wall");
    }

    return EXIT_SUCCESS;
}
/**
 * @brief Reads the Agents XML file.
 *
 * @param file The name of the file
 * @param nShapesPerAgent The number of shapes by agent (size: number of agents)
 * @param shapeIDagent A correspondence between the shape ids (index) and the agent (value) (size: number of shapes)
 * @param edges The indices of the first shape for each agent (size:  number of agents + 1)
 * @param radii The radii of all shapes (size: number of shapes)
 * @param masses The masses of the agents
 * @param mois The moment of inertia of the agents
 * @param delta_gtos The relative positions of the shapes with respect to the center of mass of each agent
 * @param materialMapping The known mapping between user-provided material ids and our ids for them
 *
 * @return EXIT_FAILURE in case of issue in the XML file (missing or unreadable field)
 *         EXIT_SUCCESS otherwise
 */
int readAgents(const std::string& file, std::vector<unsigned>& nShapesPerAgent, std::vector<unsigned>& shapeIDagent,
               std::vector<int>& edges, std::vector<double>& radii, std::vector<double>& masses, std::vector<double>& mois,
               std::vector<double2>& delta_gtos, std::map<std::string, int32_t>& materialMapping)
{
    if (agents)
    {
        for (uint32_t a = 0; a < nAgents; ++a)
        {
            delete agents[a];
            agents[a] = nullptr;
        }
        delete agents;
        agents = nullptr;
        agentMap.clear();
        agentMapInverse.clear();
        agentProperties.clear();
        shapesMaterial.clear();
    }
    tinyxml2::XMLDocument document;
    document.LoadFile(file.data());
    if (document.ErrorID() != 0)
    {
        cerr << "Error: Could not load or parse XML file" << file << endl;
        return EXIT_FAILURE;
    }

    /*  Read the Agents block   */
    tinyxml2::XMLElement* agentsElement = document.FirstChildElement("Agents");
    if (!agentsElement)
    {
        cerr << "Error: agents must be embedded in \"Agents\" tag!" << endl;
        return EXIT_FAILURE;
    }
    const tinyxml2::XMLElement* agentElement = agentsElement->FirstChildElement("Agent");
    if (!agentElement)
    {
        cerr << "Error: no Agent tag present in " << file << endl;
        return EXIT_FAILURE;
    }
    size_t sGlobal = 0;
    edges.push_back(static_cast<int>(sGlobal));
    uint32_t agentId = 0;
    while (agentElement != nullptr)
    {
        //  Id (ignored)
        const char* externId;
        if (agentElement->QueryStringAttribute("Id", &externId) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: please provide identifiers for your agents " << endl;
            return EXIT_FAILURE;
        }
        agentMap[externId] = agentId;
        agentMapInverse.emplace_back(externId);
        //  Mass and Moment of Inertia
        double mass, moi;
        if (agentElement->QueryDoubleAttribute("Mass", &mass) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: could not get mass from agent " << externId << endl;
            return EXIT_FAILURE;
        }
        if (agentElement->QueryDoubleAttribute("MomentOfInertia", &moi) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: could not get moment of inertia from agent " << externId << endl;
            return EXIT_FAILURE;
        }
        masses.push_back(mass);
        mois.push_back(moi);
        double dampingTranslational, dampingRotational;
        if (agentElement->QueryDoubleAttribute("FloorDamping", &dampingTranslational) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: for agent " << externId << ": translational damping (FloorDamping) not provided! " << endl;
            return EXIT_FAILURE;
        }
        if (agentElement->QueryDoubleAttribute("AngularDamping", &dampingRotational) != tinyxml2::XML_SUCCESS)
        {
            cerr << "Error: for agent " << externId << ": rotational damping (AngularDamping) not provided! " << endl;
            return EXIT_FAILURE;
        }
        if (dampingTranslational == 0.0 || dampingRotational == 0.0)
        {
            cerr << "Error: you must input non-zero dampings for each agent: " << endl;
            return EXIT_FAILURE;
        }
        agentProperties.emplace_back(dampingTranslational, dampingRotational);

        //  Shapes
        const tinyxml2::XMLElement* shapeElement = agentElement->FirstChildElement("Shape");
        if (!shapeElement)
        {
            cerr << "Error: an agent has no shapes in " << file << endl;
            return EXIT_FAILURE;
        }
        size_t s = 0;
        while (shapeElement != nullptr)
        {
            //  Fill shapeIDagent - as many agentIds as there are shapes for it
            shapeIDagent.push_back(agentId);
            //  Fetch material
            const char* materialId = nullptr;
            if (shapeElement->QueryStringAttribute("MaterialId", &materialId) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: no material mentioned for agent in " << file << endl;
                return EXIT_FAILURE;
            }
            if (!materialMapping.contains(materialId))
            {
                cerr << "Error: unknown material id " << materialId << "given for one of the shapes." << endl;
                return EXIT_FAILURE;
            }
            else
                shapesMaterial[sGlobal] = materialMapping[materialId];

            double radius;
            if (shapeElement->QueryDoubleAttribute("Radius", &radius) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: could not get radius from shape " << s + 1 << " in agent " << agentId << endl;
                return EXIT_FAILURE;
            }
            radii.push_back(radius);
            const char* buffer = nullptr;
            if (shapeElement->QueryStringAttribute("Position", &buffer) != tinyxml2::XML_SUCCESS)
            {
                cerr << "Error: Could not parse shape coordinates from XML file " << file << endl;
                return EXIT_FAILURE;
            }
            auto [rc, coordinates] = parse2DComponents(buffer);
            if (rc != EXIT_SUCCESS)
            {
                cerr << "Error: Could not parse shape coordinates from XML file " << file << endl;
                return EXIT_FAILURE;
            }
            delta_gtos.emplace_back(coordinates);

            shapeElement = shapeElement->NextSiblingElement("Shape");
            s++;
            sGlobal++;
        }
        nShapesPerAgent.push_back(s);
        edges.push_back(static_cast<int>(sGlobal));

        agentElement = agentElement->NextSiblingElement("Agent");
        agentId++;
    }

    nAgents = masses.size();

    return EXIT_SUCCESS;
}

/**
 * @brief Computes the normal stiffness (k_n)
 *
 * @param i Internal material id i
 * @param j Internal material id j
 *
 * @return The value of k_n
 */
double computeStiffnessNormal(const uint32_t i, const uint32_t j)
{
    const double Ei = intrinsicProperties[YOUNG_MODULUS][i];
    const double Ej = intrinsicProperties[YOUNG_MODULUS][j];
    const double Gi = intrinsicProperties[SHEAR_MODULUS][i];
    const double Gj = intrinsicProperties[SHEAR_MODULUS][j];

    return 1 / ((4 * Gi - Ei) / (4 * pow(Gi, 2)) + (4 * Gj - Ej) / (4 * pow(Gj, 2)));
}
/**
 * @brief Computes the tangential stiffness (k_t)
 *
 * @param i Internal material id i
 * @param j Internal material id j
 *
 * @return The value of k_t
 */
double computeStiffnessTangential(const uint32_t i, const uint32_t j)
{
    const double Ei = intrinsicProperties[YOUNG_MODULUS][i];
    const double Ej = intrinsicProperties[YOUNG_MODULUS][j];
    const double Gi = intrinsicProperties[SHEAR_MODULUS][i];
    const double Gj = intrinsicProperties[SHEAR_MODULUS][j];

    return 1 / ((6 * Gi - Ei) / (8 * pow(Gi, 2)) + (6 * Gj - Ej) / (8 * pow(Gj, 2)));
}

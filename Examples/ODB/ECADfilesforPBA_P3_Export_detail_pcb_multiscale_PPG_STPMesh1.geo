SetFactory("OpenCASCADE");
        Mesh.CharacteristicLengthMin = 0.1;
        Mesh.CharacteristicLengthMax = 0.1;

        a() = ShapeFromFile("/home/koopark/serviceApptainers/appt313/opt/pyKooCAE/Examples/ODB/ECADfilesforPBA_P3_Export_detail_pcb_multiscale_PPG_STPMesh1.brep");
        
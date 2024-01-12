import unittest
import main


class TestMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_repository_name(self):
        url = 'git@github.com:codespecs/daikon.git'
        self.assertEqual(main.get_repository_name(url), 'daikon')

        url = 'git@github.com:kelloggm/specimin.git'
        self.assertEqual(main.get_repository_name(url), 'specimin')

        url = 'git@github.com:typetools/checker-framework.git'
        self.assertEqual(main.get_repository_name(url), 'checker-framework')

        url = 'git@github.com:awslabs/aws-kms-compliance-checker.git'
        self.assertEqual(main.get_repository_name(url), 'aws-kms-compliance-checker')

        url = 'git@github.com:awslabs/aws-kms-compliance-checker.git' 
        self.assertNotEqual(main.get_repository_name(url), 'aws-km-compliance-checker')
    
    def test_build_specimin_command(self):
        proj_name = 'cassandra'
        root = 'src/java'
        package = 'org.apache.cassandra.index.sasi.conf'
        targets = [{
                    "method": "getMode(ColumnMetadata, Map<String, String>)",
                    "file": "IndexMode.java"
                   }]
        specimin_dir = 'user/specimin'
        target_dir = 'user/ISSUES/cf-6077'
        command = main.build_specimin_command(proj_name, target_dir, specimin_dir, root, package, targets)
        target_command = ''
        with open('resources/specimin_command_cf-6077.txt','r') as file:
            target_command = file.read()
        self.assertEqual(command, target_command)

        proj_name = 'kafka-sensors'
        root = 'src/main/java/'
        package = 'com.fillmore_labs.kafka.sensors.serde.confluent.interop'
        targets = [{
                    "method": "transform(String, byte[])",
                    "file": "Avro2Confluent.java"
                   }]
        specimin_dir = 'user/specimin'
        target_dir = 'user/ISSUES/cf-6019'
        command = main.build_specimin_command(proj_name, target_dir, specimin_dir, root, package, targets)
        with open('resources/specimin_command_cf-6019.txt','r') as file:
            target_command = file.read()
        self.assertEqual(command, target_command)




if __name__ == '__main__':
    unittest.main()
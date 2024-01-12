import unittest
import main
import shutil

class TestMain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # cloning the specimin 
        main.clone_repository('git@github.com:kelloggm/specimin.git', 'resources')

    @classmethod
    def tearDownClass(cls):
        # deleting specimin from resources
        try:
            shutil.rmtree('resources/specimin')
        except Exception as e:
            print(f"Error occurred {e}")

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
 
    def test_run_specimin(self):
        proj_name = 'test_proj'
        root = ''
        package = 'com.example'
        targets = [{
                    "method": "bar()",
                    "file": "Simple.java"
                   }]
        specimin_dir = 'resources/specimin'
        target_dir = 'resources/onefilesimple'

        command = main.build_specimin_command(proj_name, target_dir, specimin_dir, root, package, targets)
        result = main.run_specimin(command, 'resources/specimin')
        self.assertTrue(result)




if __name__ == '__main__':
    unittest.main()
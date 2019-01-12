from tests.base import ApiDBTestCase

from zou.app.models.entity import Entity
from zou.app.models.metadata_descriptor import MetadataDescriptor
from zou.app.models.project_status import ProjectStatus
from zou.app.services import projects_service
from zou.app.services.exception import ProjectNotFoundException


class ProjectServiceTestCase(ApiDBTestCase):

    def setUp(self):
        super(ProjectServiceTestCase, self).setUp()

        self.generate_fixture_project_status()
        self.generate_fixture_project_closed_status()
        self.generate_fixture_project()
        self.generate_fixture_project_closed()

    def test_get_open_projects(self):
        projects = projects_service.open_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual("Cosmos Landromat", projects[0]["name"])

    def test_get_projects(self):
        projects = projects_service.get_projects()
        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0]["project_status_name"], "Open")

    def test_get_or_create_status(self):
        project_status = projects_service.get_or_create_status("Frozen")
        statuses = ProjectStatus.query.all()
        self.assertEqual(project_status["name"], "Frozen")
        self.assertEqual(len(statuses), 3)

        project_status = projects_service.get_or_create_status("Frozen")
        self.assertEqual(project_status["name"], "Frozen")
        self.assertEqual(len(statuses), 3)

    def test_get_or_create_open_status(self):
        project_status = projects_service.get_or_create_open_status()
        self.assertEqual(project_status["name"], "Open")

    def test_save_project_status(self):
        statuses = projects_service.save_project_status(["Frozen", "Postponed"])
        self.assertEqual(len(statuses), 2)
        statuses = ProjectStatus.query.all()
        self.assertEqual(len(statuses), 4)

        statuses = projects_service.save_project_status(["Frozen", "Postponed"])
        self.assertEqual(len(statuses), 2)
        statuses = ProjectStatus.query.all()
        self.assertEqual(len(statuses), 4)

    def test_get_or_create_project(self):
        project = projects_service.get_or_create_project("Agent 327")
        projects = projects_service.get_projects()
        self.assertIsNotNone(project["id"])
        self.assertEqual(project["name"], "Agent 327")
        self.assertEqual(len(projects), 3)

    def test_get_project_by_name(self):
        project = projects_service.get_project_by_name(self.project.name)
        self.assertEqual(project["name"], self.project.name)
        self.assertRaises(
            ProjectNotFoundException,
            projects_service.get_project_by_name,
            "missing"
        )

    def test_get_project(self):
        project = projects_service.get_project(self.project.id)
        self.assertEqual(project["name"], self.project.name)
        self.assertRaises(
            ProjectNotFoundException,
            projects_service.get_project,
            "wrongid"
        )

    def test_update_project(self):
        new_name = "New name"
        projects_service.update_project(self.project.id, {"name": new_name})
        project = projects_service.get_project(self.project.id)
        self.assertEqual(project["name"], new_name)

    def test_add_team_member(self):
        self.generate_fixture_person()
        projects_service.add_team_member(self.project.id, self.person.id)
        project = projects_service.get_project(self.project.id)
        self.assertEqual(project["team"], [str(self.person.id)])

    def test_remove_team_member(self):
        self.generate_fixture_person()
        projects_service.add_team_member(self.project.id, self.person.id)
        projects_service.remove_team_member(self.project.id, self.person.id)
        project = projects_service.get_project(self.project.id)
        self.assertEqual(project["team"], [])

    def test_add_asset_metadata_descriptor(self):
        descriptor = projects_service.add_metadata_descriptor(
            self.project.id,
            "Asset",
            "Is Outdoor"
        )
        self.assertIsNotNone(MetadataDescriptor.get(descriptor["id"]))
        descriptor = projects_service.add_metadata_descriptor(
            self.project.id,
            "Asset",
            "Contractor"
        )
        descriptors = projects_service.get_metadata_descriptors(
            self.project.id,
            "Asset"
        )
        self.assertEqual(len(descriptors), 2)
        self.assertEqual(descriptors[0]["id"], descriptor["id"])
        self.assertEqual(descriptors[0]["field_name"], "contractor")
        self.assertEqual(descriptors[1]["field_name"], "is_outdoor")

    def test_update_metadata_descriptor(self):
        asset = self.generate_fixture_asset_type()
        asset = self.generate_fixture_asset()
        descriptor = projects_service.add_metadata_descriptor(
            self.project.id,
            "Asset",
            "Contractor"
        )
        asset.update({
            "data": {
                "contractor": "contractor 1"
            }
        })
        self.assertTrue("contractor" in asset.data)
        projects_service.update_metadata_descriptor(
            descriptor["id"],
            {"name": "Team"}
        )
        descriptors = projects_service.get_metadata_descriptors(
            self.project.id,
            "Asset"
        )
        self.assertEqual(len(descriptors), 1)
        asset = Entity.get(asset.id)
        self.assertEqual(asset.data.get("team"), "contractor 1")

    def test_add_delete_metadata_descriptor(self):
        asset = self.generate_fixture_asset_type()
        asset = self.generate_fixture_asset()
        descriptor = projects_service.add_metadata_descriptor(
            self.project.id,
            "Asset",
            "Contractor"
        )
        asset.update({
            "data": {
                "contractor": "contractor 1"
            }
        })
        self.assertTrue("contractor" in asset.data)

        projects_service.remove_metadata_descriptor(
            descriptor["id"]
        )
        descriptors = projects_service.get_metadata_descriptors(
            self.project.id,
            "Asset"
        )
        self.assertEqual(len(descriptors), 0)
        asset = Entity.get(asset.id)
        self.assertFalse("contractor" in asset.data)

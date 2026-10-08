import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

# resume_exploder.py
#
# Explodes a single resume.yaml into a directory tree (one file per item) plus
# a _manifest.yaml that records ORDER + INCLUSION and carries the document-level
# fields that never become their own files.
#
# The manifest is the strict source of truth for the inverse operation
# (resume_imploder.py). Contract goal: implode(explode(x)) == x

# Document-level fields that are NOT part of any exploded section. They live
# only in the manifest's `document` block so the round-trip stays lossless.
SECTION_KEYS = {
    'contact_info',
    'professional_summary',
    'key_achievements',
    'companies',
    'achievements',
    'education',
    'hobbies',
    'skills',
}

# Top-level section order emitted into the manifest (and thus the order implode
# reconstructs the resume in).
SECTION_ORDER = [
    'contact_info',
    'professional_summary',
    'key_achievements',
    'companies',
    'achievements',
    'education',
    'hobbies',
    'skills',
]


class ResumeExploder():
    def __init__(self, resume_pth: str, output_dir: Path = 'resume'):
        self.resume_data = self.load_resume_data(resume_pth)
        self.output_dir = Path(output_dir)
        # Manifest is assembled as sections are written, then dumped at the end.
        self.manifest: Dict[str, Any] = self.build_manifest()

    # ------------------------------------------------------------------ helpers
    def _write_yaml(self, relative_path: str, data: Any) -> None:
        """Write `data` to a YAML file (relative to output_dir), creating dirs."""
        full_path = self.output_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=float('inf'))

    def _update_yaml(self, relative_path: str, data: Any) -> None:
        """Write `data` to a YAML file (relative to output_dir), creating dirs."""
        full_path = self.output_dir / relative_path
        if not full_path.exists():
            self._write_yaml(relative_path, data)
        else:
            with open(full_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            for k in existing_data:
                if k not in data:
                    data[k] = existing_data[k]
            self._write_yaml(relative_path, data)

    def load_resume_data(self, file_path: str) -> Dict[str, Any]:
        """
        Load resume data from a YAML (or JSON) file.

        Args:
            file_path: Path to resume file

        Returns:
            Resume data dictionary
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                self.resume_data = yaml.safe_load(f)
            except yaml.YAMLError:
                f.seek(0)
                self.resume_data = json.load(f)

        return self.resume_data

    # ------------------------------------------------------------------ sections
    def setup_contact_info(self) -> None:
        self._write_yaml('contact_info/contact_information.yaml',
                         self.resume_data['contact_info'])

    def setup_professional_summary(self) -> None:
        self._write_yaml('professional_summary/professional_summary.yaml',
                         self.resume_data['professional_summary'])

    def setup_hobbies(self) -> None:
        for hobby in self.resume_data.get('hobbies', []):
            self._write_yaml(f"hobbies/{hobby['id']}.yaml", hobby)

    def setup_skills(self) -> None:
        for skillset in self.resume_data.get('skills', {}):
            self._write_yaml(f"skills/{skillset}.yaml", self.resume_data['skills'][skillset])

    def setup_companies(self) -> None:

        key_achievements = self.resume_data.get('key_achievements', [])
        key_achievements = {achieve['achievement_id']: achieve['content'] for achieve in key_achievements}

        for company in self.resume_data.get('companies', []):
            company_id = company['id']
            self._write_yaml(f"companies/{company_id}/company_info.yaml", company)
            for achievement in self.resume_data.get('achievements', []):
                if achievement['company_id'] == company_id:
                    if achievement['id'] in key_achievements:
                        achievement['key_achievement'] = key_achievements[achievement['id']]
                    self._update_yaml(f"companies/{company_id}/achievements/{achievement['id']}.yaml",
                        achievement)

    def setup_education(self) -> None:
        for education in self.resume_data.get('education', []):
            if education['type'] == 'degree':
                self._write_yaml(
                    f"education/degrees/{education['id']}.yaml", education)
            if education['type'] == 'certificate':
                self._write_yaml(
                    f"education/certificates/{education['id']}.yaml", education)

    # ------------------------------------------------------------------ manifest
    def _achievement_ids_for(self, company_id: str) -> List[str]:
        """Ordered achievement ids belonging to a company (source order)."""
        return [
            a['id']
            for a in self.resume_data.get('achievements', [])
            if a['company_id'] == company_id
        ]

    def build_manifest(self) -> Dict[str, Any]:
        """
        Assemble the manifest: ORDER + INCLUSION of every id-bearing item, plus
        the document-level fields that are not exploded into their own files.
        """
        data = self.resume_data
        manifest: Dict[str, Any] = {}

        # Document-level fields: everything that is NOT a known section.
        document = {k: v for k, v in data.items() if k not in SECTION_KEYS}
        if document:
            manifest['document'] = document

        # Top-level section order (only sections actually present).
        manifest['order'] = [s for s in SECTION_ORDER if s in data]

        # Single-file sections map to their one file.
        if 'contact_info' in data:
            manifest['contact_info'] = 'contact_info/contact_information.yaml'
        if 'professional_summary' in data:
            manifest['professional_summary'] = 'professional_summary/professional_summary.yaml'

        # companies -> ordered ids, each with its ordered achievement ids.
        if 'key_achievements' in data:
            manifest['key_achievements'] = [el['achievement_id'] for el in data['key_achievements']]

        # companies -> ordered ids, each with its ordered achievement ids.
        if 'companies' in data:
            manifest['companies'] = [
                {
                    'id': company['id'],
                    'achievements': self._achievement_ids_for(company['id']),
                }
                for company in data['companies']
            ]

        # education -> split by type, preserving source order within each.
        if 'education' in data:
            manifest['education'] = {
                'degrees': [
                    e['id'] for e in data['education']
                    if e['type'] == 'degree'
                ],
                'certificates': [
                    e['id'] for e in data['education']
                    if e['type'] == 'certificate'
                ],
            }

        # hobbies / skills -> ordered id / skillset-name lists.
        if 'hobbies' in data:
            manifest['hobbies'] = [h['id'] for h in data['hobbies']]

        if 'skills' in data:
            manifest['skills'] = list(data['skills'].keys())

        self.manifest = manifest
        return manifest

    def write_manifest(self) -> None:
        with open('manifest.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(self.manifest, f, sort_keys=False, allow_unicode=True)

    # ------------------------------------------------------------------ driver
    def explode(self) -> None:
        """Explode all sections and write the manifest."""
        self.setup_contact_info()
        self.setup_professional_summary()
        self.setup_hobbies()
        self.setup_skills()
        self.setup_companies()
        self.setup_education()
        self.write_manifest()


def main():
    parser = argparse.ArgumentParser(
        description='Explode a resume.yaml into a directory tree + manifest')
    parser.add_argument('--resume', required=True, help='Resume file')
    parser.add_argument('--output-dir', default='resume',
                        help='Directory to write the exploded resume (default: resume)')
    args = parser.parse_args()

    exploder = ResumeExploder(args.resume, output_dir=args.output_dir)
    exploder.explode()
    print(f"Exploded {args.resume} -> {args.output_dir}")


if __name__ == "__main__":
    main()

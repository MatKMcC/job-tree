import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List
import glob

import yaml

# resume_imploder.py
#
# Inverse of resume_exploder.py. Reads an exploded resume directory that
# contains a _manifest.yaml (the strict source of truth for order + inclusion)
# and reconstructs the original resume.yaml dictionary.
#
# Contract goal: implode(explode(x)) == x
#
# The manifest is authoritative:
#   - Only items listed in the manifest are imploded.
#   - Items are emitted in exactly the order the manifest lists them.
#   - Document-level fields that were never exploded into files (loose
#     top-level keys + the metadata block) are carried in manifest['document'].


class ResumeImploder:
    def __init__(self, resume_dir: str, manifest: str, output: str):
        self.resume_dir = Path(resume_dir)
        self.manifest = self._load_yaml(Path(manifest))
        self.output = Path(output)

    # ------------------------------------------------------------------ helpers
    def _load_yaml(self, path: Path) -> Any:
        """Load a YAML file relative to the resume directory."""
        if not path.exists():
            raise FileNotFoundError(f"Manifest references missing file: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_attribute(self, relative_path: str) -> Any:
        """Load a YAML file relative to the resume directory."""
        full_path = self.resume_dir / relative_path
        return self._load_yaml(full_path)

    # ------------------------------------------------------------------ sections
    def implode_contact_info(self) -> Any:
        rel = self.manifest['contact_info']
        return self._load_attribute(rel)

    def implode_professional_summary(self) -> Any:
        rel = self.manifest['professional_summary']
        return self._load_attribute(rel)

    def implode_key_achievements(self) -> List[Dict[str, Any]]:
        """
        Reconstruct the FLAT top-level `achievements` list.

        In the source data achievements are a single flat list (each carrying a
        `company_id`). On disk they are nested under each company. We walk the
        manifest company-by-company, then achievement-by-achievement, preserving
        order, and flatten them back out.
        """
        key_achievements = []
        seen_ids = set()

        # crawl achievements to get all achievement_ids -> content
        files = [Path(f) for f in glob.glob("companies/*/achievements/*", root_dir=self.resume_dir)]
        files = [(f.name.replace('.yaml', ''), f) for f in files]
        achievements = {name: self._load_attribute(path) for name, path in files}
        for achievement_id in self.manifest.get('key_achievements', []):
            if achievement_id in achievements:
                if achievement_id in seen_ids:
                    # Duplicate id in the manifest -> the file was overwritten on
                    # explode, so we cannot recover distinct records. Warn loudly.
                    print(
                        f"WARNING: duplicate achievement id '{achievement_id}' "
                        f"(company '{achievements['company_id']}'). Only one file exists on disk; "
                        "the round-trip is lossy for this item. Fix ids in source.",
                        file=sys.stderr,)
                seen_ids.add(achievement_id)
                achievement = {
                    'achievement_id': achievement_id,
                    'company_id': achievements[achievement_id]['company_id'],
                    'content': achievements[achievement_id]['key_achievement'],
                }
                key_achievements.append(achievement)
        return key_achievements

    def implode_companies(self) -> List[Dict[str, Any]]:
        """Reconstruct the top-level `companies` list, in manifest order."""
        companies = []
        for entry in self.manifest.get('companies', []):
            company_id = entry['id']
            company = self._load_attribute(
                f"companies/{company_id}/company_info.yaml")
            companies.append(company)
        return companies

    def implode_achievements(self) -> List[Dict[str, Any]]:
        """
        Reconstruct the FLAT top-level `achievements` list.

        In the source data achievements are a single flat list (each carrying a
        `company_id`). On disk they are nested under each company. We walk the
        manifest company-by-company, then achievement-by-achievement, preserving
        order, and flatten them back out.
        """
        achievements = []
        seen_ids = set()
        for entry in self.manifest.get('companies', []):
            company_id = entry['id']
            for achievement_id in entry.get('achievements', []):
                if achievement_id in seen_ids:
                    # Duplicate id in the manifest -> the file was overwritten on
                    # explode, so we cannot recover distinct records. Warn loudly.
                    print(
                        f"WARNING: duplicate achievement id '{achievement_id}' "
                        f"(company '{company_id}'). Only one file exists on disk; "
                        "the round-trip is lossy for this item. Fix ids in source.",
                        file=sys.stderr,)
                seen_ids.add(achievement_id)
                achievement = self._load_attribute(f"companies/{company_id}/achievements/{achievement_id}.yaml")
                if 'key_achievement' in achievement:
                    achievement.pop('key_achievement')
                achievements.append(achievement)
        return achievements

    def implode_education(self) -> List[Dict[str, Any]]:
        """
        Reconstruct the top-level `education` list from degrees/ + certificates/.
        Manifest lists degrees and certificates separately; emit degrees first
        then certificates (adjust order here if a different policy is desired).
        """
        education = []
        edu_manifest = self.manifest.get('education', {})
        for degree_id in edu_manifest.get('degrees', []):
            education.append(
                self._load_attribute(f"education/degrees/{degree_id}.yaml")
            )
        for cert_id in edu_manifest.get('certificates', []):
            education.append(
                self._load_attribute(f"education/certificates/{cert_id}.yaml")
            )
        return education

    def implode_hobbies(self) -> List[Dict[str, Any]]:
        hobbies = []
        for hobby_id in self.manifest.get('hobbies', []):
            hobbies.append(self._load_attribute(f"hobbies/{hobby_id}.yaml"))
        return hobbies

    def implode_skills(self) -> Dict[str, Any]:
        """Reconstruct the `skills` dict (skillset name -> list), in order."""
        skills = {}
        for skillset in self.manifest.get('skills', []):
            skills[skillset] = self._load_attribute(f"skills/{skillset}.yaml")
        return skills

    # ------------------------------------------------------------------ assemble
    def implode(self) -> Dict[str, Any]:
        """Reconstruct the full resume dictionary from the exploded tree."""

        resume: Dict[str, Any] = {}

        # Emit sections in the order the manifest specifies. This drives the
        # top-level key order of the reconstructed resume.
        section_builders = {
            'contact_info': self.implode_contact_info,
            'professional_summary': self.implode_professional_summary,
            'key_achievements': self.implode_key_achievements,
            'companies': self.implode_companies,
            'achievements': self.implode_achievements,
            'education': self.implode_education,
            'hobbies': self.implode_hobbies,
            'skills': self.implode_skills,
        }

        order = self.manifest.get('order', list(section_builders.keys()))
        for section in order:
            builder = section_builders.get(section)
            if builder is None:
                print(f"WARNING: unknown section '{section}' in manifest order; skipping.",
                      file=sys.stderr)
                continue
            resume[section] = builder()

        # `achievements` is a flat top-level list in the source but is not part
        # of the `order` grouping if the author omitted it; ensure it's present.
        if 'achievements' not in resume and 'companies' in resume:
            resume['achievements'] = self.implode_achievements()

        # Merge document-level fields that never became their own files
        # (loose top-level keys + the metadata block).
        document = self.manifest.get('document', {})
        for key, value in document.items():
            resume[key] = value

        return resume

    def write_resume(self) -> None:
        """Implode and write the reconstructed resume to a YAML file."""
        resume = self.implode()
        output_path = self.output
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(resume, f, sort_keys=False, allow_unicode=True, width=float('inf'))


def main():
    parser = argparse.ArgumentParser(
        description='Implode an exploded resume directory back into a single resume.yaml'
    )
    parser.add_argument(
        '--resume-dir',
        default='resume',
        help='Directory containing the exploded resume',
    )
    parser.add_argument(
        '--manifest',
        default='manifest.yaml',
        help='Directory containing the exploded resume',
    )
    parser.add_argument(
        '--output',
        default='resume.yaml',
        help='Path to write the reconstructed resume (default: resume.yaml)',
    )
    args = parser.parse_args()
    imploder = ResumeImploder(args.resume_dir, args.manifest, args.output)
    imploder.write_resume()

if __name__ == "__main__":
    main()

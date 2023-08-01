import copy
import os
import shutil
import tempfile
import unittest

from datatrove.data import Document
from datatrove.io import LocalInputDataFolder, LocalOutputDataFolder
from datatrove.pipeline.dedup.exact_substrings import (
    DatasetToSequence,
    DedupReader,
    MergeSequences,
    read_bytes,
    sequence_reader,
)
from datatrove.pipeline.dedup.utils import ExtensionHelperES


TEXT_0 = (
    "Nuclear fusion is a reaction in which two or more atomic nuclei, usually deuterium and tritium "
    "(hydrogen variants), are combined to form one or more different atomic nuclei and subatomic particles "
    "(neutrons or protons). The difference in mass between the reactants and products is manifested as either "
    "the release or absorption of energy."
)

TEXT_1 = (
    "The Adventures of Peregrine Pickle is a picaresque novel by the Scottish author Tobias Smollett, first "
    "published in 1751 and revised and published again in 1758. It tells the story of an egotistical man who "
    "experiences luck and misfortunes in the height of 18th-century European society."
)

TEXT_2 = "A, B, C, D" * 3 + TEXT_1

TEXT_3 = "Apple, Frog, SUN" * 20 + TEXT_1 + "FIRE" * 10

TEXT_4 = (
    "This is but one truly serious philosophical problem, and that is suicide. Judging whether life is or is not worth "
    "living amounts to answering the fundamental question of philosophy. All the rest— whether or not the world has "
    "three dimensions, whether the mind has nine or twelve categories—comes afterwards. These are games; one must "
    "first answer. And if it is true, as Nietzsche claims, that a philosopher, to deserve our respect, must preach "
    "by example, you can appreciate the importance of that reply, for it will precede the definitive act. These are "
    "facts the heart can feel; yet they call for careful study before they become clear to the intellect. If I ask "
    "myself how to judge that this question is more urgent than that, I reply that one judges by the actions it "
    "entails. I have never seen anyone die for the ontological argument. Galileo, who held a scientific truth of "
    "great importance, abjured it with the greatest ease as soon as it endangered his life. In a certain sense, "
    "he did right."
)

TEXT_5 = (
    "I do believe there is only one real philosophical issue, to live or to not. Judging whether life is or is "
    "not worth living amounts to answering the fundamental question of philosophy. All the rest— whether or not "
    "the world has three dimensions, whether the mind has nine or twelve categories—comes afterwards. That is "
    "why I decided to buy a coca zero, no sugar!"
)

TEXT_6 = "A, B, C, D" * 3 + TEXT_0

TEXT_7 = (
    "333 South Wabash is a simple, rectangular International Style building, but it is unique in that the entire "
    "building was painted bright red by Eagle Painting & Maintenance Company, Inc., turning an otherwise "
    "ordinary-looking structure into one of the most eye-catching buildings in the city. It was designed by the "
    "firm of Graham, Anderson, Probst & White and was completed in 1972."
)

TEXT_8 = (
    "The guaiabero (Bolbopsittacus lunulatus) is a species of parrot in the family Psittaculidae, belonging to the "
    "monotypic genus Bolbopsittacus[2] and closely related to the lovebirds (Agapornis) and hanging parrots "
    "(Loriculus).[3] It is endemic to the Philippines and locally known as bubutok. Its common name is derived "
    "from its reputation for eating guavas."
)

TEXT_9 = (
    "The Lake of the Woods Ranger Station is a United States Forest Service compound consisting of eight "
    "buildings overlooking Lake of the Woods in the Fremont-Winema National Forests of southern Oregon. All "
    "of the ranger station structures were built by the Civilian Conservation Corps between 1937 and 1939. "
    "Today, the compound serves as a Forest Service work center, and the old ranger station office is a visitor "
    "center. The ranger station is listed on the National Register of Historic Places."
)

TEXT_10 = (
    "In 1898, the Cascade Forest Reserve was created in southern Oregon. The forest area around Lake of the Woods "
    "became part of the reserve. The forest was managed as part of that Cascade reserve until 1908, when the "
    "area was transferred to the Crater National Forest. The Forest Service issued the first residential use "
    "permit for a private cabin in the Lake of the Woods area in 1916. In 1920, the Forest Service built a "
    "public campground at the lake. The site was very popular, with 1,850 summer visitors using the campground "
    "the first year it open."
)

TEXT_11 = TEXT_10

TEXT_12 = (
    "Solo et pensoso i più deserti campi vo mesurando a passi tardi et lenti, et gli occhi porto per "
    "fuggire intenti ove vestigio human l’arena stampi."
)

TEXT_13 = TEXT_10

TEXT_14 = TEXT_10

TEXT_15 = "I am here randomly, don't pay attention to me!"

TEXT_16 = TEXT_10

TEXT_17 = "I am here because Alessandro wanted a unique message at the end"

bytearange_file = (
    "S 534\nGot 2\nS 520\nS 618\nGot 2\nS 442\nGot 2\nS 578\nS 578\nGot 2\nGot 2\nS 524\nGot 2\nS 500\n"
    "Got 2\nGot 2\nMerging.\nout\n14 158\n168 302\n303 348\n350 484\n496 768\n770 942\n980 1068\n"
    "1406 1494\n1527 1572\n1574 1718\n2291 2526\n2527 2762\n2881 3116\n3117 3352\n3389 3624\n"
)

bytearange_file_2 = (
    "S 620\nGot 2\nS 736\nS 640\nS 712\nGot 2\nS 622\nGot 2\nS 688\nGot 2\nGot 2\nS 592\nGot 2\nS 538\nGot 2\nGot 2\n"
    "Merging.\nout\n14 158\n168 302\n303 348\n350 484\n496 768\n770 942\n980 1068\n1406 1494\n1527 1572\n1574 1718\n"
    "2291 2526\n2527 2762\n2881 3116\n3117 3352\n3389 3624\n3663 3898\n3935 4168\n"
)

DATA = [
    Document(content=TEXT_0, data_id="0"),
    Document(content=TEXT_1, data_id="1"),
    Document(content=TEXT_2, data_id="2"),
    Document(content=TEXT_3, data_id="3"),
    Document(content=TEXT_4, data_id="4"),
    Document(content=TEXT_5, data_id="5"),
    Document(content=TEXT_6, data_id="6"),
    Document(content=TEXT_7, data_id="7"),
    Document(content=TEXT_8, data_id="8"),
    Document(content=TEXT_9, data_id="9"),
    Document(content=TEXT_10, data_id="10"),
    Document(content=TEXT_11, data_id="11"),
    Document(content=TEXT_12, data_id="12"),
    Document(content=TEXT_13, data_id="13"),
    Document(content=TEXT_14, data_id="14"),
    Document(content=TEXT_15, data_id="15"),
    Document(content=TEXT_16, data_id="16"),
    Document(content=TEXT_17, data_id="17"),
]

TEXT_2_0 = "I am a really random text don't pay attention to me"

data_2 = [
    Document(content=TEXT_16, data_id="0"),
    Document(content=TEXT_2_0, data_id="1"),
    Document(content=TEXT_16, data_id="2"),
]


TARGETS = {
    0: "N",
    1: "",
    2: " D",
    3: "Apple SUN",
    4: TEXT_4[:72] + TEXT_4[307:],
    5: TEXT_5[:74] + TEXT_5[309:],
    6: " DN",
    7: TEXT_7,
    8: TEXT_8,
    9: TEXT_9,
    10: "",
    11: "",
    12: TEXT_12,
    13: "",
    14: "",
    15: TEXT_15,
    16: "",
    17: TEXT_17,
}

TARGETS_2 = {0: "", 1: TEXT_2_0, 2: ""}


class TestExactSubstr(unittest.TestCase):
    def match_doc(self, sequence, size, reader, docs):
        for i, doc_content in enumerate(sequence_reader(sequence, size)):
            self.assertEqual(docs[i].content, reader.tokenizer.decode(read_bytes(doc_content)))

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_signature_1_worker(self):
        with open(self.test_dir + "/test" + ExtensionHelperES.stage_3_bytes_ranges, "w") as f:
            f.write(bytearange_file)
        data = copy.deepcopy(DATA)

        dataset_to_sequence = DatasetToSequence(output_folder=LocalOutputDataFolder(path=self.test_dir))
        merge_sequence = MergeSequences(
            input_folder=LocalInputDataFolder(path=self.test_dir),
            output_folder=LocalOutputDataFolder(path=self.test_dir),
            tasks_stage_1=1,
        )

        dedup_reader = DedupReader(
            data_folder=LocalInputDataFolder(path=self.test_dir),
            sequence_folder=LocalInputDataFolder(path=self.test_dir),
            min_doc_words=0,
        )

        # test quality of stage 1, 2 output
        dataset_to_sequence(data=data)
        merge_sequence(data=[])
        big_sequence_path = self.test_dir + "/dataset" + ExtensionHelperES.stage_2_big_sequence
        self.assertTrue(os.path.isfile(big_sequence_path))

        dedup_reader.rank = 0
        dedup_reader.read_bytes_offset()
        bytes_offset = dedup_reader.bytes_offset
        with open(os.path.join(self.test_dir, "00000.es_sequence"), "rb") as f_s:
            with open(os.path.join(self.test_dir, "dataset.big_sequence"), "rb") as f_b:
                sequence = f_s.read()
                self.assertEqual(sequence, f_b.read())
                self.assertEqual(len(sequence), bytes_offset[1])

        sequence_file, size_file = dedup_reader.get_all_files(0, 1)
        for i, doc_content in enumerate(sequence_reader(sequence_file, size_file)):
            self.assertEqual(data[i].content, dedup_reader.tokenizer.decode(read_bytes(doc_content)))

        self.match_doc(sequence_file, size_file, dedup_reader, docs=data)

        # test if  deduplication actually works
        for i, doc in enumerate(dedup_reader(data=data)):
            self.assertEqual(doc.content, TARGETS.get(i))

    def test_signature_2_worker(self):
        data = copy.deepcopy(DATA)

        with open(self.test_dir + "/test" + ExtensionHelperES.stage_3_bytes_ranges, "w") as f:
            f.write(bytearange_file_2)

        dataset_to_sequence = DatasetToSequence(output_folder=LocalOutputDataFolder(path=self.test_dir))
        merge_sequence = MergeSequences(
            input_folder=LocalInputDataFolder(path=self.test_dir),
            output_folder=LocalOutputDataFolder(path=self.test_dir),
            tasks_stage_1=2,
        )

        dedup_reader = DedupReader(
            data_folder=LocalInputDataFolder(path=self.test_dir),
            sequence_folder=LocalInputDataFolder(path=self.test_dir),
            min_doc_words=0,
        )

        # test quality of stage 1, 2 output
        dataset_to_sequence(data=DATA, rank=0)
        dataset_to_sequence(data=data_2, rank=1)
        merge_sequence(data=[])

        big_sequence_path = self.test_dir + "/dataset" + ExtensionHelperES.stage_2_big_sequence
        self.assertTrue(os.path.isfile(big_sequence_path))

        dedup_reader.rank = 0
        dedup_reader.read_bytes_offset()
        bytes_offset = dedup_reader.bytes_offset
        with open(os.path.join(self.test_dir, "00001.es_sequence"), "rb") as f_1:
            with open(os.path.join(self.test_dir, "00000.es_sequence"), "rb") as f_0:
                with open(os.path.join(self.test_dir, "dataset.big_sequence"), "rb") as f_b:
                    sequence_0 = f_0.read()
                    sequence_1 = f_1.read()
                    self.assertEqual(sequence_0 + sequence_1, f_b.read())
                    self.assertEqual(len(sequence_0) + len(sequence_1), bytes_offset[2])

        sequence_file_0, size_file_0 = dedup_reader.get_all_files(0, 2)
        sequence_file_1, size_file_1 = dedup_reader.get_all_files(1, 2)

        self.match_doc(sequence_file_0, size_file_0, dedup_reader, data)
        self.match_doc(sequence_file_1, size_file_1, dedup_reader, data_2)

        # test if  deduplication actually works
        for i, doc in enumerate(dedup_reader(data=data, rank=0, world_size=2)):
            self.assertEqual(doc.content, TARGETS.get(i))

        for i, doc in enumerate(dedup_reader(data=data_2, rank=1, world_size=2)):
            self.assertEqual(doc.content, TARGETS_2.get(i))
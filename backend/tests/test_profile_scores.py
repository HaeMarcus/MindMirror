import unittest

from app.profile_scores import BIG_FIVE_KEYS, stabilize_profile_scores


class ProfileScoreTests(unittest.TestCase):
    def test_initial_scores_are_spread_without_changing_order(self):
        profile = {"big_five": {
            "openness": 58,
            "conscientiousness": 55,
            "extraversion": 52,
            "agreeableness": 56,
            "neuroticism": 48,
        }}
        result = stabilize_profile_scores(profile)
        scores = result["big_five"]
        self.assertGreaterEqual(max(scores.values()) - min(scores.values()), 20)
        self.assertGreater(scores["openness"], scores["agreeableness"])
        self.assertGreater(scores["agreeableness"], scores["neuroticism"])

    def test_updates_are_visible_but_limited(self):
        old = {"big_five": {key: 50 for key in BIG_FIVE_KEYS}}
        new = {"big_five": {
            "openness": 51,
            "conscientiousness": 90,
            "extraversion": 47,
            "agreeableness": 50,
            "neuroticism": 5,
        }}
        result = stabilize_profile_scores(new, old)["big_five"]
        self.assertEqual(result["openness"], 52)
        self.assertEqual(result["conscientiousness"], 56)
        self.assertEqual(result["extraversion"], 47)
        self.assertEqual(result["agreeableness"], 50)
        self.assertEqual(result["neuroticism"], 44)


if __name__ == "__main__":
    unittest.main()

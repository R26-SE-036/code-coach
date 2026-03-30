from app.feature_extractor import extract_features

sample_code = """
public class Test {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3};

        for (int i = 0; i <= arr.length; i++) {
            if (i = 2) {
                System.out.println(arr[arr.length]);
            }
        }
    }
}
""".strip()

features = extract_features(sample_code)

for key, value in sorted(features.items()):
    print(f"{key}: {value}")
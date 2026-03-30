package data.ml.raw_snippets.off_by_one.buggy;

public class OffByOneBug002 {
    public static void main(String[] args) {
        int[] numbers = { 10, 20, 30, 40 };

        for (int i = 0; i <= numbers.length; i++) {
            System.out.println("Value: " + numbers[i]);
        }
    }
}
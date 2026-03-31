package data.ml.raw_snippets.clean;

public class Clean005 {
    public static void main(String[] args) {
        int[] scores = { 60, 70, 80 };
        int total = 0;

        for (int score : scores) {
            total += score;
        }

        System.out.println(total);
    }
}
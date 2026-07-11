public class GenArrayIndexFix022 {
    static int lastOf(int[] scores) {
        return scores[scores.length - 1];
    }

    static void printAll1(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}

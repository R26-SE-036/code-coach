public class GenCleanBoundaryMinusOne018 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static int tally(int[] values) {
        int total = 0;
        for (int i = 0; i <= values.length - 1; i++) {
            total += values[i];
        }
        return total;
    }
}

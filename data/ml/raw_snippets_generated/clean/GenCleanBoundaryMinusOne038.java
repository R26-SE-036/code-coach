public class GenCleanBoundaryMinusOne038 {
    static void printAll1(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static int tally(int[] ages) {
        int total = 0;
        for (int i = 0; i <= ages.length - 1; i++) {
            total += ages[i];
        }
        return total;
    }

    static int sum2(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}

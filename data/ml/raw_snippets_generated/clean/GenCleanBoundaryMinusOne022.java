public class GenCleanBoundaryMinusOne022 {
    static void printAll1(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static int tally(int[] marks) {
        int total = 0;
        for (int i = 0; i <= marks.length - 1; i++) {
            total += marks[i];
        }
        return total;
    }
}

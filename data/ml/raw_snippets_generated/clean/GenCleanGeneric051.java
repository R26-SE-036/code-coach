public class GenCleanGeneric051 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static void printAll2(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}

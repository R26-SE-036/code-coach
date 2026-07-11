public class GenOffByOneBug066 {
    static int addUp(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static void printAll2(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }
}

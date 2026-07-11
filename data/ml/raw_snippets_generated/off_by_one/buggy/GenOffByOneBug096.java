public class GenOffByOneBug096 {
    static int[] duplicate(int[] ages) {
        int[] copy = new int[ages.length];
        for (int i = 0; i <= ages.length; i++) {
            copy[i] = ages[i];
        }
        return copy;
    }

    static int drain1(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static int sum2(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }
}

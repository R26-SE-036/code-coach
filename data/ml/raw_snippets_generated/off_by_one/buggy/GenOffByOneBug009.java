public class GenOffByOneBug009 {
    static int[] duplicate(int[] totals) {
        int[] copy = new int[totals.length];
        for (int i = 0; i <= totals.length; i++) {
            copy[i] = totals[i];
        }
        return copy;
    }
}

public class GenCleanTailIndex008 {
    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static int tail(int[] totals) {
        return totals[totals.length - 1];
    }
}

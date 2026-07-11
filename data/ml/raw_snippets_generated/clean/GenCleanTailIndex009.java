public class GenCleanTailIndex009 {
    static int tail(int[] totals) {
        return totals[totals.length - 1];
    }

    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }
}

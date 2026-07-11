public class GenWhileNoUpdateBug009 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static void countdown(int limit) {
        while (limit > 0) {
            System.out.println("left: " + limit);
        }
    }
}

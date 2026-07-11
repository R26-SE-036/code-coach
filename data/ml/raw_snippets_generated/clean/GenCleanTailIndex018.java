public class GenCleanTailIndex018 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int tail(int[] scores) {
        return scores[scores.length - 1];
    }

    static int drain2(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }
}

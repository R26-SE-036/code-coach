public class GenIncorrectConditionalBug080 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static int drain2(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static void announce(int steps) {
        if (steps = 100) {
            System.out.println("hit the target");
        }
    }
}

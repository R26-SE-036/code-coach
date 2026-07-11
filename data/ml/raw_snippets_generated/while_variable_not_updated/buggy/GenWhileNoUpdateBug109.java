public class GenWhileNoUpdateBug109 {
    static int gather(int points, int steps) {
        int sum = 0;
        while (points < steps) {
            sum += points;
        }
        return sum;
    }

    static int drain1(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static boolean isEven2(int level) {
        return level % 2 == 0;
    }
}

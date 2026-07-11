public class GenWhileNoUpdateFix065 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int gather(int limit, int steps) {
        int sum = 0;
        while (limit < steps) {
            sum += limit;
            limit++;
        }
        return sum;
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

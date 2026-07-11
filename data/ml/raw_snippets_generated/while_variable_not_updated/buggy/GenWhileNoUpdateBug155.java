public class GenWhileNoUpdateBug155 {
    static void pump(boolean ready, int stock) {
        while (!ready) {
            System.out.println(stock);
            stock++;
        }
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}

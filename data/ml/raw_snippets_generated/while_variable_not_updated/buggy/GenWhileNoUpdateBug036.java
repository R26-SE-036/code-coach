public class GenWhileNoUpdateBug036 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int gather(int limit, int count) {
        int sum = 0;
        while (limit < count) {
            sum += limit;
        }
        return sum;
    }
}

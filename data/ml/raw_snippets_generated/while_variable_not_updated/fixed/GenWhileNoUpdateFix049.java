public class GenWhileNoUpdateFix049 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void countdown(int steps) {
        while (steps > 0) {
            System.out.println("left: " + steps);
            steps--;
        }
    }

    static void printAll2(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }
}

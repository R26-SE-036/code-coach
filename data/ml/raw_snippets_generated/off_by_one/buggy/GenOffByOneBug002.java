public class GenOffByOneBug002 {
    static String describe1(int steps) {
        if (steps < 10) {
            return "low";
        } else if (steps > 50) {
            return "high";
        }
        return "medium";
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void show(int[] values) {
        for (int i = 0; i <= values.length; i++) {
            System.out.println(values[i]);
        }
    }
}

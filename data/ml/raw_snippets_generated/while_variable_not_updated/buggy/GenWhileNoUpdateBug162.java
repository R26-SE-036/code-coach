public class GenWhileNoUpdateBug162 {
    static int sum1(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
        }
    }

    static void printAll2(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }
}

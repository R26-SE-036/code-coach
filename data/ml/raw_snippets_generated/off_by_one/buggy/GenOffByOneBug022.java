public class GenOffByOneBug022 {
    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static boolean isEven2(int limit) {
        return limit % 2 == 0;
    }

    static void show(int[] values) {
        for (int i = 0; i <= values.length; i++) {
            System.out.println(values[i]);
        }
    }
}

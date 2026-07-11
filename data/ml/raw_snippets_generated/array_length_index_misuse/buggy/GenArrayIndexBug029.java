public class GenArrayIndexBug029 {
    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static void showLast(int[] sizes) {
        System.out.println(sizes[sizes.length]);
    }
}

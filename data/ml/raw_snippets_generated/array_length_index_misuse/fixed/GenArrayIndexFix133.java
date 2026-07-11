public class GenArrayIndexFix133 {
    static int lastOf(int[] sizes) {
        return sizes[sizes.length - 1];
    }

    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static boolean isEven2(int limit) {
        return limit % 2 == 0;
    }
}

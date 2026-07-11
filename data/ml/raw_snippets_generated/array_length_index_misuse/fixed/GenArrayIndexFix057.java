public class GenArrayIndexFix057 {
    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length - 1] = value;
    }

    static void printAll1(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }
}

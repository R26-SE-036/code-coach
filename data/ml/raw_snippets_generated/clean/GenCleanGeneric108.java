public class GenCleanGeneric108 {
    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static void printAll3(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }
}

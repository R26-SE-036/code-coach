public class GenWhileNoUpdateFix085 {
    static void printAll1(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static int drain2(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int sum3(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int largest4(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static int gather(int attempts, int total) {
        int sum = 0;
        while (attempts < total) {
            sum += attempts;
            attempts++;
        }
        return sum;
    }
}

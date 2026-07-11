public class GenCleanScannerLoop004 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static boolean isEven2(int points) {
        return points % 2 == 0;
    }

    static boolean isEven3(int limit) {
        return limit % 2 == 0;
    }

    static void readAll(java.util.Scanner scanner) {
        while (scanner.hasNextLine()) {
            System.out.println(scanner.nextLine());
        }
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll6(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int largest7(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static int drain8(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }
}

public class GenCleanWhileTrueBreak011 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static boolean isEven2(int steps) {
        return steps % 2 == 0;
    }

    static int spin(int steps) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > steps) {
                break;
            }
        }
        return rounds;
    }
}

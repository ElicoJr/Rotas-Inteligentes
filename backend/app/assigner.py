# backend/app/assigner.py
from datetime import timedelta
import numpy as np
import copy

def greedy_assign(df_priority, garages_df, shifts_df, time_matrix_garage_to_service, service_duration_col='duration_min'):
    """
    Greedy assignment:
    - df_priority: prioritized services (ordered by score desc). Services are indexed 0..N-1.
    - garages_df: garages with index mapping to rows in time_matrix_garage_to_service
    - shifts_df: shifts with 'crew', 'start', 'end', 'shift_minutes' fields
    - time_matrix_garage_to_service: G x N matrix (minutes)
    Returns: dict crew -> list of service indices
    """

    N = df_priority.shape[0]
    G = len(garages_df)
    assignments = {shift['crew']: [] for _, shift in shifts_df.iterrows()}

    # compute remaining minutes per crew
    shift_remaining = {}
    crew_garage_index = {}
    for _, shift in shifts_df.iterrows():
        crew = shift['crew']
        shift_remaining[crew] = shift['shift_minutes']
        # map garage index: assume garages_df has id mapping; here we use integer order
        crew_garage_index[crew] = shift.get('garage_index', 0)

    # iterate services in priority order
    for idx, srv in df_priority.reset_index().iterrows():
        svc_idx = idx  # corresponds to column in time_matrix
        best_crew = None
        best_cost = None
        for _, shift in shifts_df.iterrows():
            crew = shift['crew']
            garage_idx = crew_garage_index[crew]
            travel_time = time_matrix_garage_to_service[garage_idx][svc_idx]
            service_time = float(srv[service_duration_col])
            total_req = travel_time + service_time
            if total_req <= shift_remaining[crew]:
                # cost metric: prefer crew with smallest incremental time (or consider other metrics)
                if best_cost is None or total_req < best_cost:
                    best_cost = total_req
                    best_crew = crew
        if best_crew is not None:
            assignments[best_crew].append(svc_idx)
            shift_remaining[best_crew] -= best_cost
        else:
            # no crew fits respecting shift -> leave unassigned for now
            # Could push to overflow list
            pass

    return assignments, shift_remaining

def repair_assign(assignments, df_priority, shifts_df, time_matrix_garage_to_service):
    """
    Simple repair: if any crew exceeded shift (shouldn't happen in greedy), reassign lowest-score service
    """
    # placeholder — greedy ensures no overtime. Implement advanced repair if using GA crossover/mutation.
    return assignments

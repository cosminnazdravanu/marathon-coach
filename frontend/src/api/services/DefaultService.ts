/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Read Root
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readRootGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
    /**
     * Connect Strava
     * @returns any Successful Response
     * @throws ApiError
     */
    public static connectStravaConnectStravaGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/connect_strava',
        });
    }
    /**
     * Disconnect Strava
     * @returns any Successful Response
     * @throws ApiError
     */
    public static disconnectStravaDisconnectStravaPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/disconnect_strava',
        });
    }
    /**
     * Strava Callback
     * @param code
     * @returns any Successful Response
     * @throws ApiError
     */
    public static stravaCallbackStravaCallbackGet(
        code?: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/strava_callback',
            query: {
                'code': code,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Activity Feedback
     * @param activityId
     * @returns string Successful Response
     * @throws ApiError
     */
    public static activityFeedbackActivityFeedbackGet(
        activityId?: string,
    ): CancelablePromise<string> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/activity_feedback',
            query: {
                'activity_id': activityId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
